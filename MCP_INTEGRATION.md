# MCP PowerPoint Integration

Ce document explique l'intégration du serveur MCP PowerPoint avec le système de chat.

## Fonctionnalité

Le système détecte automatiquement les demandes de génération PowerPoint et utilise l'outil MCP approprié pour créer des présentations structurées.

## Architecture

```
Chat System
├── message_service.py     # Détecte les demandes PowerPoint
├── openai_service.py      # Gère les appels d'outils via API OpenAI-compatible
├── mcp_service.py         # Coordonne les outils MCP
└── backend/mcp/powerpoint_mcp/
    ├── mcp_server.py      # Serveur MCP PowerPoint
    ├── src/               # Logique de génération PowerPoint
    └── config.py          # Configuration Mistral
```

## Installation

1. **Installer les dépendances MCP:**
   ```bash
   ./install_mcp_dependencies.sh
   ```

2. **Configurer la clé API Mistral:**
   ```bash
   # Dans backend/mcp/powerpoint_mcp/.env
   MISTRAL_API_KEY=votre_clé_mistral_ici
   ```

3. **Vérifier la configuration:**
   ```bash
   cd backend/mcp/powerpoint_mcp
   uv run python -c "from config import config; print('✅ Config OK' if config.validate_api_key() else '❌ API key manquante')"
   ```

## Utilisation

### Déclenchement Automatique

Le système détecte automatiquement ces mots-clés dans les messages utilisateur :
- `powerpoint`, `ppt`
- `présentation`, `presentation`  
- `slides`, `diapositives`
- `générer un powerpoint`, `crée un powerpoint`
- `create powerpoint`, `generate powerpoint`
- `faire une présentation`

### Exemples de Requêtes

```
Utilisateur: "peux-tu générer un powerpoint sur l'intelligence artificielle?"
→ Système: Utilise generate_powerpoint_from_text avec le contenu IA

Utilisateur: "crée une présentation sur les meilleures pratiques en développement"
→ Système: Génère un PowerPoint avec slides structurées

Utilisateur: "fait moi des slides sur les énergies renouvelables" 
→ Système: Crée une présentation complète avec données et statistiques
```

## Outils MCP Disponibles

### `generate_powerpoint_from_text`

**Description:** Génère une présentation PowerPoint à partir de texte

**Paramètres:**
- `text` (requis): Contenu à convertir en présentation
- `title` (optionnel): Titre de la présentation
- `output_format` (optionnel): "json", "pptx", ou "both" (défaut)
- `refine` (optionnel): Affiner le JSON généré (défaut: true)
- `theme_suggestion` (optionnel): Suggestion de thème

**Sortie:**
- Présentation PowerPoint (.pptx)
- Structure JSON (optionnel)
- Métadonnées (nombre de slides, durée estimée, etc.)

## Flux d'Exécution

1. **Détection:** `mcp_service.should_use_powerpoint_tool()` analyse le message
2. **Préparation:** `mcp_service.get_available_tools()` fournit les outils Mistral
3. **Appel IA:** Mistral API reçoit les outils et décide de les utiliser
4. **Exécution:** `mcp_service.execute_powerpoint_generation()` crée la présentation
5. **Formatage:** `mcp_service.format_powerpoint_response()` prépare la réponse utilisateur

## Réponse Structurée

Quand un PowerPoint est généré, l'utilisateur reçoit :

```
**Présentation PowerPoint générée avec succès !**

**Détails de la présentation :**
- **Titre :** Intelligence Artificielle - Vue d'ensemble
- **Nombre de slides :** 8
- **Thème :** Professionnel
- **Durée estimée :** 15 minutes

**Sujets principaux couverts :**
• Introduction à l'IA
• Apprentissage automatique
• Applications pratiques
• Défis et opportunités
• Futur de l'IA

**Fichier PowerPoint créé :**
- **Nom du fichier :** Intelligence_Artificielle_Vue_d_ensemble.pptx
- **Taille :** 2.3 MB
- **Chemin :** /tmp/tmpxyz123/presentation.pptx

**Votre présentation est prête à être utilisée !**
```

## Débogage

### Vérifier l'Installation MCP
```bash
cd backend/mcp/powerpoint_mcp
uv run python mcp_server.py --help
```

### Tester la Génération Directement
```bash
cd backend/mcp/powerpoint_mcp  
uv run python -c "
from src.converter import PowerPointConverter
converter = PowerPointConverter()
result = converter.convert_text('Test presentation about AI')
print(f'Generated {result.metadata.total_slides} slides')
"
```

### Logs du Service
Les logs du service MCP sont visibles dans les logs du backend principal :
```bash
grep "PowerPoint\|MCP\|Tool" backend/logs/app.log
```

## Sécurité

- **API Keys:** Stockées dans `.env`, jamais exposées côté client
- **Fichiers Temporaires:** Générés dans `/tmp`, nettoyés automatiquement
- **Validation:** Tous les inputs sont validés via Pydantic schemas
- **Rate Limiting:** Appliqué au niveau du service principal

## Performance

- **Cache:** Réponses mises en cache pendant 10 minutes
- **Async:** Toutes les opérations sont asynchrones
- **Streaming:** Simulation de streaming pour les réponses avec outils
- **Optimisation:** Génération parallèle JSON + PPTX

## Extensions Futures

- Support d'autres formats (PDF, Google Slides)
- Templates personnalisés
- Import depuis documents existants
- Génération collaborative multi-agents
- API REST directe pour les outils MCP

## Notes Techniques

- **MCP Version:** 1.0.0+
- **Mistral API:** Compatible function calling
- **Python:** 3.11+ (utilise `uv` pour la gestion des dépendances)
- **Async:** Full async/await pattern
- **Error Handling:** Graceful fallback en cas d'erreur MCP
