#!/usr/bin/env python3
"""
Test script pour vérifier l'intégration du modèle de vision en mode local avec vLLM.
Permet de tester n'importe quel VLM (Pixtral, MiniCPM, InternVL, ...) exposé via vLLM.
"""

import asyncio
import base64
import os
from pathlib import Path
import logging
from app.services.vllm_service import VLLMService
from app.config import settings

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_vision_local():
    """Test de l'analyse d'image avec le modèle de vision en mode local"""
    
    print(f"\n🔧 Configuration actuelle:")
    print(f"   - Mode LLM: {settings.llm_mode}")
    print(f"   - Vision vLLM URL: {settings.vision_vllm_url}")
    print(f"   - Vision vLLM Model: {settings.vision_vllm_model}")
    
    # Vérifier qu'on est bien en mode local
    if settings.llm_mode != "local":
        print("\n⚠️  ATTENTION: Le mode LLM n'est pas configuré sur 'local'")
        print("   Mettez LLM_MODE=local dans votre fichier .env")
        return
    
    # Créer une image de test simple
    print("\n📸 Création d'une image de test...")
    test_image_path = Path("test_image.png")
    
    # Si vous avez une image de test, remplacez ce bloc
    if not test_image_path.exists():
        print("❌ Aucune image de test trouvée. Créez un fichier 'test_image.png'")
        return
    
    # Encoder l'image en base64
    with open(test_image_path, 'rb') as f:
        image_data = f.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    print(f"✅ Image encodée: {len(image_base64)} caractères")
    
    # Initialiser le service vLLM
    print("\n🚀 Initialisation du service vLLM...")
    vllm_service = VLLMService()
    
    # Vérifier la santé du service de vision
    print("\n🏥 Vérification de la santé du service de vision...")
    is_healthy = await vllm_service.vision_health_check()
    if is_healthy:
        print("✅ Service de vision vLLM accessible")
    else:
        print("❌ Service de vision vLLM inaccessible")
        print(f"   Vérifiez que le serveur est lancé sur {settings.vision_vllm_url}")
        return
    
    # Tester l'analyse d'image
    print("\n🎨 Test d'analyse d'image avec le modèle de vision local...")
    try:
        prompt = "Décris cette image en détail. Qu'est-ce que tu vois ?"
        result = await vllm_service.process_image_with_vision_model(image_base64, prompt)
        
        print("\n✅ Analyse réussie !")
        print(f"\n📝 Résultat ({len(result)} caractères):")
        print("-" * 50)
        print(result)
        print("-" * 50)
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'analyse: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_pdf_processing():
    """Test du traitement PDF avec le modèle de vision local"""
    from app.utils.document_processors import process_document_to_text
    
    print("\n\n📄 Test de traitement PDF avec modèle de vision local...")
    
    # Chercher un PDF de test
    test_pdf_path = Path("test_document.pdf")
    if not test_pdf_path.exists():
        print("❌ Aucun PDF de test trouvé. Créez un fichier 'test_document.pdf'")
        return
    
    try:
        print(f"📊 Traitement du PDF: {test_pdf_path}")
        result = await process_document_to_text(str(test_pdf_path), "application/pdf")
        
        print(f"\n✅ Traitement réussi !")
        print(f"\n📝 Résultat ({len(result)} caractères):")
        print("-" * 50)
        print(result[:1000] + "..." if len(result) > 1000 else result)
        print("-" * 50)
        
    except Exception as e:
        print(f"\n❌ Erreur lors du traitement PDF: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    """Fonction principale de test"""
    print("🧪 Test du modèle de vision en mode local avec vLLM")
    print("=" * 60)
    
    # Test 1: Analyse d'image simple
    await test_vision_local()
    
    # Test 2: Traitement PDF (optionnel)
    # await test_pdf_processing()
    
    print("\n\n✅ Tests terminés !")

if __name__ == "__main__":
    # Pour exécuter: python test_vision_local.py
    asyncio.run(main())
