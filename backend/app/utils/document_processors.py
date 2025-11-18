import asyncio
from pathlib import Path
from typing import Optional, List, Callable, Awaitable, Dict, Any
import aiofiles
import PyPDF2
import docx
import io
import base64
from mistralai import Mistral
import os
import tempfile
from pdf2image import convert_from_path
from PIL import Image
import logging
from zipfile import ZipFile


async def _call_pixtral_api(messages):
    """Appelle le modèle Pixtral avec fallback si le modèle configuré est invalide."""
    from app.config import settings

    client = Mistral(api_key=settings.mistral_api_key)
    preferred_model = settings.pixtral_model
    fallback_model = "pixtral-large-latest"

    async def _invoke(model_name: str):
        return await asyncio.to_thread(
            client.chat.complete,
            model=model_name,
            messages=messages,
        )

    try:
        return await _invoke(preferred_model)
    except Exception as e:
        message = str(e)
        if "invalid_model" in message and preferred_model != fallback_model:
            logger.warning(
                "❗ Modèle Pixtral %s invalide, tentative avec fallback %s",
                preferred_model,
                fallback_model,
            )
            return await _invoke(fallback_model)
        raise

# Configurer le logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


MIN_SIGNIFICANT_IMAGE_AREA = 64000  # ≈ 250x250 px


async def _emit_progress(
    callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]],
    payload: Dict[str, Any],
) -> None:
    if not callback:
        return
    try:
        await callback(payload)
    except Exception as exc:
        logger.debug("Progress callback raised an exception: %s", exc)

async def process_document_to_text(
    file_path: str,
    file_type: str,
    progress_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
) -> str:
    """
    Convertit différents types de documents en texte brut
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Fichier non trouvé: {file_path}")
    
    # Déterminer le type de traitement selon le type MIME ou l'extension
    ext = file_path.suffix.lower()
    
    await _emit_progress(
        progress_callback,
        {
            "stage": "text_extraction",
            "stage_label": "Extraction du texte",
            "progress": 0.05,
            "message": "Préparation de l'extraction",
        },
    )

    if ext in ['.txt', '.md']:
        content = await _process_text_file(file_path)
        await _emit_progress(
            progress_callback,
            {
                "stage": "text_extraction",
                "stage_label": "Extraction du texte",
                "progress": 0.6,
                "message": "Texte extrait",
            },
        )
        return content
    elif ext == '.pdf' or 'pdf' in file_type:
        return await _process_pdf_file(file_path, progress_callback=progress_callback)
    elif ext in ['.docx', '.doc'] or 'word' in file_type:
        return await _process_docx_file(file_path, progress_callback=progress_callback)
    elif ext == '.rtf':
        content = await _process_rtf_file(file_path)
        await _emit_progress(
            progress_callback,
            {
                "stage": "text_extraction",
                "stage_label": "Extraction du texte",
                "progress": 0.6,
                "message": "Texte extrait",
            },
        )
        return content
    elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp'] or 'image' in file_type:
        return await _process_image_file_with_pixtral(file_path, progress_callback=progress_callback)
    else:
        # Par défaut, essayer de lire comme texte
        content = await _process_text_file(file_path)
        await _emit_progress(
            progress_callback,
            {
                "stage": "text_extraction",
                "stage_label": "Extraction du texte",
                "progress": 0.6,
                "message": "Texte extrait",
            },
        )
        return content

async def _process_text_file(file_path: Path) -> str:
    """Lit un fichier texte"""
    async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return await f.read()

async def _process_pdf_file(
    file_path: Path,
    progress_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
) -> str:
    """Extrait le texte d'un PDF - utilise une approche hybride"""
    from app.config import settings
    
    # D'abord, essayer l'extraction de texte classique avec PyPDF2
    def extract_pdf_text():
        text = []
        has_images = False
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text() or ""

                if page_text.strip():
                    text.append(f"Page {page_num + 1}:\n{page_text}")
                else:
                    has_images = True

                # Inspecter les XObjects pour détecter des images même si on a déjà du texte
                try:
                    resources = page.get("/Resources")
                    if resources is not None:
                        try:
                            resources = resources.get_object()
                        except Exception:
                            pass
                    if isinstance(resources, dict):
                        xobjects = resources.get("/XObject")
                        if xobjects is not None:
                            try:
                                xobjects_dict = xobjects.get_object()
                            except Exception:
                                xobjects_dict = xobjects
                            if isinstance(xobjects_dict, dict):
                                for obj in xobjects_dict.values():
                                    try:
                                        xobj = obj.get_object() if hasattr(obj, "get_object") else obj
                                        subtype = xobj.get("/Subtype")
                                    except Exception:
                                        continue
                                    if subtype == "/Image":
                                        width = xobj.get("/Width") or 0
                                        height = xobj.get("/Height") or 0
                                        try:
                                            area = int(width) * int(height)
                                        except Exception:
                                            area = 0
                                        if area >= MIN_SIGNIFICANT_IMAGE_AREA:
                                            has_images = True
                                            break
                                        logger.debug(
                                            "Ignoring small PDF image on page %d (%d px²)",
                                            page_num + 1,
                                            area,
                                        )
                except Exception:
                    # Si l'inspection échoue, on ne bloque pas le flux
                    pass
        return '\n'.join(text), has_images
    
    loop = asyncio.get_event_loop()
    extracted_text, has_potential_images = await loop.run_in_executor(None, extract_pdf_text)
    
    # Si le PDF semble contenir des images ou peu de texte, utiliser Pixtral
    if has_potential_images or len(extracted_text.strip()) < settings.pdf_use_pixtral_threshold:
        logger.info(f"📊 PDF nécessite Pixtral - Texte extrait: {len(extracted_text.strip())} caractères (seuil: {settings.pdf_use_pixtral_threshold})")
        if has_potential_images:
            logger.info("🖼️ Images détectées dans le PDF")
        
        try:
            pixtral_text = await _process_pdf_with_pixtral(
                file_path,
                max_pages=settings.pdf_max_pages_pixtral,
                progress_callback=progress_callback,
            )
            # Combiner les deux approches si on a du texte des deux côtés
            if extracted_text.strip() and pixtral_text.strip():
                logger.info(f"🔀 Combinaison extraction texte + Pixtral")
                await _emit_progress(
                    progress_callback,
                    {
                        "stage": "vision_analysis",
                        "stage_label": "Analyse visuelle (Pixtral)",
                        "progress": 0.7,
                        "message": "Analyse visuelle terminée",
                    },
                )
                return (
                    "=== Analyse visuelle (Pixtral) ===\n"
                    f"{pixtral_text}\n\n"
                    "=== Texte extrait ===\n"
                    f"{extracted_text}"
                )
            elif pixtral_text.strip():
                logger.info(f"🎨 Utilisation Pixtral seul")
                await _emit_progress(
                    progress_callback,
                    {
                        "stage": "vision_analysis",
                        "stage_label": "Analyse visuelle (Pixtral)",
                        "progress": 0.7,
                        "message": "Analyse visuelle terminée",
                    },
                )
                return pixtral_text
        except Exception as e:
            logger.error(f"❌ Erreur traitement PDF avec Pixtral: {e}")
            # Fallback sur le texte extrait
    else:
        logger.info(f"📝 PDF traité avec extraction de texte simple ({len(extracted_text.strip())} caractères)")
    await _emit_progress(
        progress_callback,
        {
            "stage": "text_extraction",
            "stage_label": "Extraction du texte",
            "progress": 0.6,
            "message": "Extraction du texte PDF terminée",
        },
    )
    return extracted_text

async def _process_docx_file(
    file_path: Path,
    progress_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
) -> str:
    """Extrait le texte d'un fichier DOCX et traite les images embarquées"""

    def extract_docx_text() -> str:
        doc = docx.Document(file_path)
        text = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text.append(paragraph.text)
        return '\n'.join(text)

    loop = asyncio.get_event_loop()
    text_content = await loop.run_in_executor(None, extract_docx_text)

    image_sections: List[str] = []
    has_images = False

    try:
        with ZipFile(file_path, 'r') as archive:
            media_files = [name for name in archive.namelist() if name.startswith('word/media/')]
            if media_files:
                significant_images: List[tuple[str, bytes]] = []
                skipped_small = 0

                for name in media_files:
                    try:
                        data = archive.read(name)
                    except KeyError:
                        logger.warning(f"Image {name} introuvable dans l'archive DOCX")
                        continue

                    try:
                        with Image.open(io.BytesIO(data)) as pil_img:
                            width, height = pil_img.size
                            area = width * height
                    except Exception:
                        area = MIN_SIGNIFICANT_IMAGE_AREA  # Fallback: traiter

                    if area < MIN_SIGNIFICANT_IMAGE_AREA:
                        skipped_small += 1
                        logger.debug(
                            "Skipping small DOCX image %s (%d px²)",
                            name,
                            area,
                        )
                        continue

                    significant_images.append((name, data))

                total_images = len(significant_images)
                has_images = total_images > 0

                if total_images == 0:
                    logger.info("Aucune image significative détectée dans le DOCX")
                else:
                    progress_start = 0.2
                    progress_end = 0.7
                    progress_span = max(progress_end - progress_start, 0.05)
                    await _emit_progress(
                        progress_callback,
                        {
                            "stage": "vision_analysis",
                            "stage_label": "Analyse visuelle (Pixtral)",
                            "current": 0,
                            "total": total_images,
                            "progress": progress_start,
                            "message": f"Analyse des images (0/{total_images})",
                        },
                    )

                    with tempfile.TemporaryDirectory() as temp_dir:
                        temp_dir_path = Path(temp_dir)
                        for idx, (name, data) in enumerate(significant_images, start=1):
                            suffix = Path(name).suffix or '.png'
                            image_path = temp_dir_path / f"docx_image_{idx}{suffix}"

                            try:
                                async with aiofiles.open(image_path, 'wb') as img_file:
                                    await img_file.write(data)
                            except Exception as e:
                                logger.error(f"❌ Impossible d'écrire l'image DOCX {name}: {e}")
                                continue

                            try:
                                transcription = await _process_image_file_with_pixtral(
                                    image_path,
                                    progress_callback=progress_callback,
                                    position=idx,
                                    total=total_images,
                                )
                                if transcription and transcription.strip():
                                    image_sections.append(
                                        f"Image {idx} ({Path(name).name}):\n{transcription}"
                                    )
                                await _emit_progress(
                                    progress_callback,
                                    {
                                        "stage": "vision_analysis",
                                        "stage_label": "Analyse visuelle (Pixtral)",
                                        "current": idx,
                                        "total": total_images,
                                        "progress": progress_start + (idx / max(total_images, 1)) * progress_span,
                                        "message": f"Analyse des images ({idx}/{total_images})",
                                    },
                                )
                            except Exception as e:
                                logger.error(f"❌ Erreur lors de l'analyse Pixtral de l'image DOCX {name}: {e}")

                if skipped_small:
                    await _emit_progress(
                        progress_callback,
                        {
                            "stage": "vision_analysis",
                            "stage_label": "Analyse visuelle (Pixtral)",
                            "progress": progress_start,
                            "message": f"{skipped_small} image(s) ignorée(s) car trop petites",
                        },
                    )
    except Exception as e:
        logger.warning(f"⚠️ Impossible d'extraire les images du DOCX: {e}")

    if has_images and image_sections:
        await _emit_progress(
            progress_callback,
            {
                "stage": "vision_analysis",
                "stage_label": "Analyse visuelle (Pixtral)",
                "progress": 0.7,
                "message": "Analyse visuelle terminée",
            },
        )
        if text_content.strip():
            return (
                "=== Analyse visuelle (Pixtral) ===\n"
                + "\n\n".join(image_sections)
                + "\n\n=== Texte extrait ===\n"
                + text_content
            )
        return "\n\n".join(image_sections)

    await _emit_progress(
        progress_callback,
        {
            "stage": "text_extraction",
            "stage_label": "Extraction du texte",
            "progress": 0.6,
            "message": "Texte extrait",
        },
    )

    return text_content

async def _process_rtf_file(file_path: Path) -> str:
    """Traite un fichier RTF (simplifié - nécessiterait une lib spécialisée pour un support complet)"""
    # Pour l'instant, traiter comme texte brut
    # Dans un cas réel, utiliser striprtf ou python-rtf
    return await _process_text_file(file_path)

async def _process_image_file_with_pixtral(
    file_path: Path,
    progress_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
    position: Optional[int] = None,
    total: Optional[int] = None,
) -> str:
    """Utilise Pixtral pour analyser et transcrire le contenu d'une image"""
    from app.config import settings
    
    logger.info(f"🎨 Début analyse Pixtral pour: {file_path.name}")
    single_asset = position is None or total is None
    progress_start = 0.2 if single_asset else None
    progress_end = 0.7 if single_asset else None
    if single_asset:
        await _emit_progress(
            progress_callback,
            {
                "stage": "vision_analysis",
                "stage_label": "Analyse visuelle (Pixtral)",
                "current": 0,
                "total": 1,
                "progress": progress_start,
                "message": "Analyse visuelle de l'image",
            },
        )
    logger.info(f"🔧 Mode LLM: {settings.llm_mode}")
    
    # Encoder l'image en base64
    logger.info(f"🔐 Encodage de l'image en base64...")
    async with aiofiles.open(file_path, 'rb') as f:
        image_data = await f.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')
    logger.info(f"✅ Image encodée: {len(base64_image)} caractères")
    
    # Déterminer le type MIME de l'image
    ext = file_path.suffix.lower()
    mime_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    mime_type = mime_types.get(ext, 'image/jpeg')
    
    # Déterminer si on utilise le mode API ou local
    if settings.llm_mode == "local":
        # Mode local : utiliser vLLM avec Pixtral
        logger.info(f"🚀 Utilisation de Pixtral local (vLLM)")
        from app.services.vllm_service import VLLMService
        
        try:
            vllm_service = VLLMService()
            prompt = (
                "Analyse cette image avec le plus de précision possible. Commence par identifier le type de visuel "
                "(photo, illustration, capture d'écran, tableau, slide, document scanné, etc.). "
                "Ensuite, retranscris mot pour mot tout le texte lisible. Pour un tableau ou un formulaire, "
                "restitue les en-têtes et les valeurs cellule par cellule. Pour une capture d'écran, explique "
                "l'application ou le site montré, les sections visibles et le déroulé exact de la conversation ou des "
                "données affichées. Pour un paysage ou une scène photo, décris en détail les éléments, leurs positions, "
                "les couleurs, l'ambiance, ainsi que toute information contextuelle implicite (moment de la journée, "
                "activité en cours, public visé, etc.). Termine par un résumé synthétique et les informations clés à "
                "retenir. Organise ta réponse avec des sections claires (Type d'image, Texte exact, Description détaillée, "
                "Résumé, Informations clés)."
            )
            
            result = await vllm_service.process_image_with_pixtral(base64_image, prompt)
            logger.info(f"✅ Pixtral local a retourné {len(result)} caractères")
            logger.info(f"📄 Aperçu: {result[:200]}...")
            await _emit_progress(
                progress_callback,
                {
                    "stage": "vision_analysis",
                    "stage_label": "Analyse visuelle (Pixtral)",
                    "current": position or 1,
                    "total": total or 1,
                    "progress": progress_end,
                    "message": "Analyse visuelle terminée",
                },
            )
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur Pixtral local: {str(e)}", exc_info=True)
            return f"Erreur lors de l'analyse de l'image avec Pixtral local: {str(e)}"
    else:
        # Mode API : utiliser Mistral API
        logger.info(f"🚀 Appel API Pixtral avec modèle: {settings.pixtral_model}")
        # Construire l'URL data de l'image
        image_url = f"data:{mime_type};base64,{base64_image}"
        
        try:
            response = await _call_pixtral_api(
                [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyse cette image et fais une transcription complète et détaillée de son contenu. 
                                Si l'image contient du texte, transcris-le exactement. 
                                Si l'image contient des éléments visuels (graphiques, schémas, photos), décris-les de manière détaillée.
                                Si c'est une capture d'écran, décris l'interface et transcris tout le texte visible.
                                Organise ta réponse de manière structurée."""
                            },
                            {
                                "type": "image_url",
                                "image_url": image_url
                            }
                        ]
                    }
                ]
            )
            
            # Extraire la transcription de la réponse
            if response.choices and len(response.choices) > 0:
                result = response.choices[0].message.content
                logger.info(f"✅ Pixtral API a retourné {len(result)} caractères")
                logger.info(f"📄 Aperçu: {result[:200]}...")
                await _emit_progress(
                    progress_callback,
                    {
                        "stage": "vision_analysis",
                        "stage_label": "Analyse visuelle (Pixtral)",
                        "current": position or 1,
                        "total": total or 1,
                        "progress": progress_end,
                        "message": "Analyse visuelle terminée",
                    },
                )
                return result
            else:
                logger.error("❌ Pixtral API n'a retourné aucune réponse")
                return "Erreur: Aucune transcription générée par Pixtral"
            
        except Exception as e:
            logger.error(f"❌ Erreur Pixtral: {str(e)}", exc_info=True)
            return f"Erreur lors de l'analyse de l'image avec Pixtral: {str(e)}"

async def _process_pdf_with_pixtral(
    file_path: Path,
    max_pages: int = 0,
    progress_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
) -> str:
    """Convertit les pages PDF en images et les analyse avec Pixtral"""
    from app.config import settings
    
    logger.info(f"📑 Début traitement PDF avec Pixtral: {file_path.name}")
    logger.info(f"🔧 Mode LLM: {settings.llm_mode}")
    
    # Initialiser le service approprié selon le mode
    if settings.llm_mode == "local":
        from app.services.vllm_service import VLLMService
        vllm_service = VLLMService()
        logger.info("📊 Utilisation de Pixtral local pour PDF")
    else:
        logger.info(f"📊 Utilisation de Pixtral API pour PDF (modèle: {settings.pixtral_model})")
    
    results = []
    
    # Créer un dossier temporaire pour les images
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Convertir le PDF en images (limitées à max_pages pour éviter de traiter des PDFs énormes)
            if max_pages > 0:
                logger.info(f"🖼️ Conversion PDF en images (max {max_pages} pages)...")
                convert_kwargs = {"first_page": 1, "last_page": max_pages, "dpi": 150}
            else:
                logger.info("🖼️ Conversion PDF en images (toutes les pages)...")
                convert_kwargs = {"dpi": 150}
            images = await asyncio.to_thread(
                convert_from_path,
                str(file_path),
                **convert_kwargs,
            )
            total_pages = len(images)
            logger.info(f"✅ {total_pages} pages converties")
            progress_start = 0.2
            progress_end = 0.7
            progress_span = max(progress_end - progress_start, 0.05)
            await _emit_progress(
                progress_callback,
                {
                    "stage": "vision_analysis",
                    "stage_label": "Analyse visuelle (Pixtral)",
                    "current": 0,
                    "total": total_pages,
                    "progress": progress_start,
                    "message": f"Analyse des pages (0/{total_pages})",
                },
            )
            
            # Traiter chaque page avec Pixtral
            for i, image in enumerate(images):
                logger.info(f"📄 Traitement page {i+1}/{total_pages}...")
                await _emit_progress(
                    progress_callback,
                    {
                        "stage": "vision_analysis",
                        "stage_label": "Analyse visuelle (Pixtral)",
                        "current": i,
                        "total": total_pages,
                        "progress": progress_start + (i / max(total_pages, 1)) * progress_span,
                        "message": f"Analyse de la page {i+1}/{total_pages}",
                    },
                )
                # Sauvegarder temporairement l'image
                temp_image_path = Path(temp_dir) / f"page_{i+1}.png"
                await asyncio.to_thread(image.save, str(temp_image_path), 'PNG')
                
                # Encoder en base64
                async with aiofiles.open(temp_image_path, 'rb') as f:
                    image_data = await f.read()
                    base64_image = base64.b64encode(image_data).decode('utf-8')
                
                # Analyser avec Pixtral (API ou local selon le mode)
                try:
                    prompt = (
                        f"Analyse la page {i+1} de ce PDF en suivant les directives suivantes : identifie d'abord le type de "
                        "contenu visuel principal (document imprimé, capture d'écran, diapositive, photo, tableau, etc.). "
                        "Transcris ensuite mot pour mot tout le texte lisible. Pour les tableaux, restitue les colonnes et "
                        "les lignes avec leurs valeurs exactes. Pour les captures d'écran, explique le contexte (application, "
                        "sites ou interlocuteurs) et détaille la conversation ou les données affichées. Pour les photos ou "
                        "illustrations, décris précisément les éléments visibles, leurs positions, couleurs, ambiance et "
                        "intention probable. Termine la page par un résumé synthétique et une liste d'informations clés à "
                        "retenir. Structure ta réponse avec les sections : Type de contenu, Texte exact, Description "
                        "détaillée, Résumé, Informations clés."
                    )
                    
                    page_content: Optional[str] = None

                    if settings.llm_mode == "local":
                        # Mode local : utiliser vLLM
                        page_content = await vllm_service.process_image_with_pixtral(base64_image, prompt)
                    else:
                        # Mode API : utiliser Mistral
                        image_url = f"data:image/png;base64,{base64_image}"
                        response = await _call_pixtral_api(
                            [
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": prompt
                                        },
                                        {
                                            "type": "image_url",
                                            "image_url": image_url
                                        }
                                    ]
                                }
                            ]
                        )
                        if response.choices and len(response.choices) > 0:
                            page_content = response.choices[0].message.content

                    if page_content:
                        results.append(f"\n=== Page {i+1} ===\n{page_content}")
                    else:
                        logger.warning("Pixtral n'a renvoyé aucun contenu pour la page %d", i + 1)
                        raise RuntimeError("La réponse Pixtral est vide")

                except Exception as e:
                    results.append(f"\n=== Page {i+1} ===\nErreur lors de l'analyse: {str(e)}")
                finally:
                    current_page = min(i + 1, total_pages)
                    await _emit_progress(
                        progress_callback,
                        {
                            "stage": "vision_analysis",
                            "stage_label": "Analyse visuelle (Pixtral)",
                            "current": current_page,
                            "total": total_pages,
                            "progress": progress_start + (current_page / max(total_pages, 1)) * progress_span,
                            "message": f"Analyse des pages ({current_page}/{total_pages})",
                        },
                    )
                
                # Limiter pour éviter de surcharger l'API
                if max_pages > 0 and i >= max_pages - 1:
                    if len(images) > max_pages:
                        results.append(f"\n\n[Note: PDF contient {len(images)} pages, seules les {max_pages} premières ont été analysées]")
                    break
                    
        except Exception as e:
            return f"Erreur lors de la conversion PDF en images: {str(e)}"

    await _emit_progress(
        progress_callback,
        {
            "stage": "vision_analysis",
            "stage_label": "Analyse visuelle (Pixtral)",
            "progress": 0.7,
            "message": "Analyse visuelle terminée",
        },
    )
    
    return '\n'.join(results)

def estimate_token_count(text: str) -> int:
    """
    Estime le nombre de tokens dans un texte
    Approximation: ~4 caractères par token en moyenne
    """
    return len(text) // 4

def truncate_to_token_limit(text: str, max_tokens: int = 2000) -> str:
    """
    Tronque un texte pour respecter une limite de tokens
    """
    estimated_chars = max_tokens * 4
    if len(text) <= estimated_chars:
        return text
    
    # Tronquer en gardant un peu de marge
    truncated = text[:estimated_chars - 100]
    
    # Essayer de couper à la fin d'une phrase
    last_period = truncated.rfind('.')
    last_newline = truncated.rfind('\n')
    
    cut_point = max(last_period, last_newline)
    if cut_point > estimated_chars // 2:  # Si on trouve un point de coupure raisonnable
        truncated = truncated[:cut_point + 1]
    
    return truncated + "\n\n[Document tronqué...]"
