# Intégration MCP PowerPoint

## Vue d'ensemble

L'intégration MCP PowerPoint permet au chat généraliste de détecter automatiquement les demandes de génération de présentations PowerPoint et d'utiliser l'API function calling de Mistral pour créer des présentations professionnelles.

## Architecture

### Composants Backend

1. **Service MCP** (`backend/app/services/mcp_service.py`)
   - Détecte les demandes de PowerPoint
   - Fournit les outils à Mistral
   - Exécute la génération de PowerPoint

2. **Service PowerPoint** (`backend/app/services/powerpoint_service.py`)
   - Interface avec le module MCP PowerPoint
   - Génère les présentations via Mistral
   - Gère les fichiers générés

3. **Service Mistral** (`backend/app/services/mistral_service.py`)
   - Support des function calls
   - Gère les appels d'outils MCP
   - Formate les réponses pour l'utilisateur

4. **Service Messages** (`backend/app/services/message_service.py`)
   - Détecte les besoins d'outils
   - Enrichit le prompt système
   - Passe les outils à Mistral

5. **API PowerPoint** (`backend/app/api/powerpoint.py`)
   - Endpoints REST pour la génération
   - Téléchargement des fichiers
   - Support du chat

### Composants Frontend

1. **Hook PowerPoint** (`frontend/src/hooks/usePowerPointGeneration.ts`)
   - Détection côté client
   - Gestion de la génération
   - Notifications toast

2. **Composant Result** (`frontend/src/components/chat/PowerPointResult.tsx`)
   - Affichage des résultats
   - Bouton de téléchargement
   - Interface élégante

3. **Chat Container** (`frontend/src/components/chat/ChatContainer.tsx`)
   - Intégration dans le chat
   - Génération parallèle
   - Affichage des résultats

## Flux de fonctionnement

1. **Utilisateur** : "génère un powerpoint sur les animaux"
2. **Frontend** : Détecte la demande et affiche un indicateur
3. **Backend Message Service** : Détecte les mots-clés PowerPoint
4. **MCP Service** : Fournit l'outil `generate_powerpoint_from_text` à Mistral
5. **Mistral** : Décide d'utiliser l'outil avec les bons paramètres
6. **PowerPoint Service** : Génère la présentation via l'API Mistral
7. **Réponse** : Retour formaté avec lien de téléchargement

## Configuration requise

### Variables d'environnement

```bash
# backend/.env
MISTRAL_API_KEY=your_key_here
```

### Modèle Mistral

Le système utilise `mistral-small-latest` qui supporte les function calls.

## Tests

### Test simple
```bash
python test_mcp_simple.py
```

### Test complet
```bash
python test_powerpoint_integration.py
```

## Phrases déclencheurs

Le système détecte automatiquement ces types de demandes :

- "génère un powerpoint sur..."
- "créer une présentation sur..."
- "faire des slides sur..."
- "peux-tu faire un PowerPoint..."
- Mots-clés : powerpoint, ppt, présentation, slides, diapositives

## Utilisation

1. **Démarrer le backend** avec la clé API Mistral configurée
2. **Démarrer le frontend**
3. **Dans le chat**, demander : "génère un powerpoint sur les animaux"
4. **Le système** :
   - Détecte automatiquement la demande
   - Génère la présentation via Mistral
   - Affiche le résultat avec lien de téléchargement

## 📁 Structure des fichiers générés

```
backend/uploads/powerpoints/
├── [user_id]/
│   ├── presentation_20240903_143022.pptx
│   └── ...
└── presentation_[timestamp].pptx
```

## 🔗 Endpoints API

- `POST /api/powerpoint/generate-from-text` - Génération depuis texte
- `POST /api/powerpoint/generate-from-json` - Génération depuis JSON
- `POST /api/powerpoint/generate-from-chat-message` - Génération depuis chat
- `GET /api/powerpoint/download/{file_path}` - Téléchargement

## Amélioration continue

Le système peut être étendu pour :
- Supporter d'autres formats (Google Slides, PDF)
- Ajouter des templates personnalisés
- Intégrer des images automatiquement
- Supporter plusieurs langues
- Ajouter des animations et transitions

## Dépannage

### Le système ne détecte pas la demande
- Vérifier les mots-clés dans `mcp_service.py`
- S'assurer que le message contient "powerpoint", "présentation", etc.

### Erreur de génération
- Vérifier que `MISTRAL_API_KEY` est configurée
- Vérifier les logs du backend
- S'assurer que le module MCP PowerPoint est installé

### Pas de téléchargement
- Vérifier que le dossier `uploads/powerpoints` existe
- Vérifier les permissions de fichiers
- Vérifier l'endpoint de téléchargement