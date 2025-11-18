# Guide d'utilisation - FoyerGPT

Ce guide vous accompagne dans l'utilisation de FoyerGPT, de la création de votre compte à l'utilisation avancée des agents IA.

## Table des matières

1. [Premiers pas](#premiers-pas)
2. [Créer et gérer des agents](#créer-et-gérer-des-agents)
3. [Conversations et messages](#conversations-et-messages)
4. [Utilisation des documents](#utilisation-des-documents)
5. [Fonctionnalités avancées](#fonctionnalités-avancées)
6. [Astuces et bonnes pratiques](#astuces-et-bonnes-pratiques)

## Premiers pas

### 1. Création de compte

1. Accédez à `http://localhost:8060`
2. Cliquez sur "S'inscrire"
3. Remplissez le formulaire :
   - **Email** : Votre adresse email valide
   - **Mot de passe** : Minimum 8 caractères
   - **Trigramme** : Identifiant unique de 3 lettres (ex: JDO pour Jean Dupont)
4. Cliquez sur "Créer mon compte"

### 2. Connexion

1. Utilisez votre email et mot de passe
2. Cochez "Se souvenir de moi" pour rester connecté
3. Cliquez sur "Se connecter"

### 3. Interface principale

Après connexion, vous arrivez sur l'interface principale composée de :

- **Barre latérale gauche** : Navigation et liste des conversations
- **Zone centrale** : Espace de chat
- **En-tête** : Sélection d'agent et actions

## Créer et gérer des agents

### Comprendre les agents

Les agents sont des assistants IA personnalisés avec :
- Un **prompt système** qui définit leur comportement
- Un **modèle de langage** (Mistral)
- Des **paramètres** de génération (température)
- La capacité d'**apprendre** de vos interactions

### Créer votre premier agent

1. Cliquez sur "Mes GPTs" dans la barre latérale
2. Cliquez sur "Créer un agent"
3. Remplissez les informations :

#### Informations de base
- **Nom** : Ex: "Expert Python"
- **Description** : Ex: "Assistant spécialisé en programmation Python"
- **Avatar** : Choisissez une image ou utilisez l'URL par défaut

#### Prompt système
C'est l'instruction principale de votre agent. Exemple :
```
Tu es un expert en programmation Python avec 10 ans d'expérience. 
Tu aides les développeurs à :
- Écrire du code Python propre et efficace
- Déboguer leurs programmes
- Optimiser les performances
- Suivre les meilleures pratiques (PEP 8, etc.)

Réponds de manière claire et pédagogique, avec des exemples de code quand c'est pertinent.
```

#### Configuration
- **Modèle** : 
  - `mistral-small` : Rapide, pour les tâches simples
  - `mistral-medium` : Équilibré, recommandé
  - `mistral-large` : Plus puissant, pour les tâches complexes

- **Température** (0.0 - 1.0) :
  - `0.0` : Réponses déterministes et précises
  - `0.7` : Équilibre créativité/cohérence (défaut)
  - `1.0` : Maximum de créativité

- **Apprentissage** : Activez pour que l'agent s'améliore avec vos conversations

- **Visibilité** : 
  - Privé : Seulement vous
  - Public : Disponible dans le marketplace

4. Cliquez sur "Créer l'agent"

### Modifier un agent

1. Allez dans "Mes GPTs"
2. Cliquez sur l'icône d'édition
3. Modifiez les paramètres souhaités
4. Sauvegardez les changements

### Exemples d'agents utiles

#### Assistant de code généraliste
```
Tu es un assistant de programmation polyvalent. Tu maîtrises plusieurs langages (Python, JavaScript, Java, C++, etc.) et peux aider avec :
- L'écriture de code
- Le débogage
- L'architecture logicielle
- Les choix technologiques
- L'optimisation des performances
```

#### Rédacteur professionnel
```
Tu es un rédacteur professionnel spécialisé dans la création de contenu de qualité. Tu aides à :
- Rédiger des articles et des rapports
- Améliorer le style et la grammaire
- Structurer les idées
- Adapter le ton selon l'audience
Utilise un français impeccable et propose toujours plusieurs alternatives.
```

#### Tuteur pédagogique
```
Tu es un tuteur patient et pédagogue. Ta mission est d'aider les étudiants à comprendre des concepts complexes en :
- Expliquant étape par étape
- Utilisant des analogies simples
- Posant des questions pour vérifier la compréhension
- Encourageant l'apprentissage actif
Ne donne jamais directement la réponse, guide l'étudiant vers la solution.
```

## Conversations et messages

### Démarrer une conversation

1. Sélectionnez un agent dans le menu déroulant en haut
2. Cliquez sur "Nouvelle conversation" ou utilisez `Cmd/Ctrl + K`
3. Tapez votre message dans la zone de texte
4. Appuyez sur Entrée ou cliquez sur Envoyer

### Fonctionnalités de chat

#### Formatage des messages
Utilisez le Markdown pour formater vos messages :
- `**gras**` pour du texte en gras
- `*italique*` pour de l'italique
- `` `code` `` pour du code inline
- ````python``` pour des blocs de code

#### Actions sur les messages
- **Copier** : Cliquez sur l'icône 📋 pour copier un message
- **Régénérer** : Demandez une nouvelle réponse si nécessaire

#### Gestion des conversations
- **Renommer** : Cliquez sur le titre pour le modifier
- **Supprimer** : Utilisez l'icône de suppression dans la liste
- **Exporter** : Téléchargez la conversation en format texte

### Raccourcis clavier

- `Cmd/Ctrl + K` : Nouvelle conversation
- `Cmd/Ctrl + /` : Focus sur la zone de message
- `Cmd/Ctrl + Entrée` : Envoyer le message
- `Flèches ↑↓` : Naviguer dans l'historique

## Utilisation des documents

### Types de fichiers supportés

- **Documents** : PDF, DOCX, TXT, MD
- **Images** : PNG, JPG, JPEG (avec OCR)
- **Taille maximale** : 10 MB par fichier

### Uploader un document

#### Méthode 1 : Dans une conversation
1. Cliquez sur l'icône 📎 dans la zone de message
2. Sélectionnez votre fichier
3. Le document sera analysé et son contenu intégré au contexte

#### Méthode 2 : Pour un agent
1. Allez dans "Mes GPTs"
2. Sélectionnez un agent
3. Cliquez sur "Gérer les documents"
4. Uploadez les fichiers de référence

### Cas d'usage des documents

#### Analyse de code
```
1. Uploadez votre fichier Python
2. Demandez : "Peux-tu analyser ce code et suggérer des améliorations ?"
3. L'agent examinera le code et proposera des optimisations
```

#### Résumé de documents
```
1. Uploadez un PDF de rapport
2. Demandez : "Fais-moi un résumé en 5 points clés"
3. L'agent extraira les informations principales
```

#### Traduction
```
1. Uploadez un document en anglais
2. Demandez : "Traduis ce document en français en préservant le formatage"
3. L'agent fournira une traduction professionnelle
```

## Fonctionnalités avancées

### Mode apprentissage

Quand activé sur un agent :
1. L'agent mémorise vos préférences
2. Il s'adapte à votre style de communication
3. Il améliore ses réponses au fil du temps

**Exemple** : Si vous corrigez souvent le format de code, l'agent apprendra vos conventions.

### Templates de conversation

Créez des templates réutilisables :

```python
# Template : Revue de code
"""
Analyse ce code selon les critères suivants :
1. Lisibilité et maintenabilité
2. Performance et optimisation
3. Sécurité et bonnes pratiques
4. Tests et documentation

Code à analyser :
[COLLER VOTRE CODE ICI]
"""
```

### Chaînage de requêtes

Utilisez les réponses précédentes pour approfondir :

```
Vous : "Explique-moi les générateurs Python"
Agent : [Explication détaillée]
Vous : "Maintenant, montre-moi 3 exemples pratiques"
Agent : [Exemples avec code]
Vous : "Compare les performances avec les listes"
Agent : [Analyse comparative]
```

### Mode multi-agents

Créez des agents spécialisés qui se complètent :

1. **Architecte** : Conçoit la structure
2. **Développeur** : Implémente le code
3. **Testeur** : Écrit les tests
4. **Documentaliste** : Rédige la documentation

## Astuces et bonnes pratiques

### 1. Prompts efficaces

**❌ Vague** : "Aide-moi avec Python"

**✅ Précis** : "J'ai une liste de dictionnaires Python et je veux les trier par une clé spécifique. Comment faire ?"

### 2. Contexte suffisant

**❌ Incomplet** : "Pourquoi ça ne marche pas ?"

**✅ Complet** : "J'ai cette erreur `KeyError: 'user'` quand j'exécute ce code : [code]. Le dictionnaire vient de cette API : [structure]"

### 3. Itération progressive

Au lieu de demander une solution complète :
1. Commencez par la structure générale
2. Affinez chaque partie
3. Optimisez à la fin

### 4. Utilisation des agents spécialisés

- **Tâches simples** : Agent généraliste
- **Code spécifique** : Agent spécialisé (Python, JavaScript, etc.)
- **Rédaction** : Agent rédacteur
- **Apprentissage** : Agent tuteur

### 5. Gestion des conversations longues

- Créez une nouvelle conversation pour chaque sujet distinct
- Utilisez des titres descriptifs
- Exportez les conversations importantes

### 6. Sécurité et confidentialité

- Ne partagez jamais de mots de passe ou clés API
- Anonymisez les données sensibles
- Utilisez des agents privés pour le code propriétaire

## Résolution de problèmes

### L'agent ne comprend pas ma demande

1. Reformulez avec plus de détails
2. Divisez en questions plus simples
3. Donnez des exemples de ce que vous attendez

### Réponses trop longues ou trop courtes

Précisez vos attentes :
- "Réponds en 3 points maximum"
- "Donne-moi une explication détaillée avec exemples"

### Erreurs dans le code généré

1. Copiez l'erreur complète
2. Donnez le contexte d'exécution
3. Demandez une correction spécifique

### Performance lente

- Utilisez `mistral-small` pour les tâches simples
- Évitez les conversations trop longues
- Créez de nouvelles conversations régulièrement

## Exemples de workflows complets

### Développement d'une fonctionnalité

1. **Planning** avec l'agent Architecte :
   ```
   "Je veux créer un système d'authentification JWT pour mon API FastAPI. 
   Quelles sont les étapes et les composants nécessaires ?"
   ```

2. **Implémentation** avec l'agent Python :
   ```
   "Implémente le modèle User avec SQLAlchemy pour PostgreSQL, 
   incluant email, password hashé, et timestamps"
   ```

3. **Tests** avec l'agent Testeur :
   ```
   "Écris des tests pytest pour ces endpoints d'authentification : 
   /register, /login, /refresh"
   ```

4. **Documentation** avec l'agent Rédacteur :
   ```
   "Rédige la documentation API pour ces endpoints d'authentification 
   au format OpenAPI/Swagger"
   ```

### Apprentissage d'un nouveau concept

1. **Introduction** :
   ```
   "Explique-moi les décorateurs Python comme si j'étais débutant"
   ```

2. **Exemples progressifs** :
   ```
   "Montre-moi un décorateur simple qui mesure le temps d'exécution"
   ```

3. **Cas avancés** :
   ```
   "Comment créer un décorateur avec paramètres ?"
   ```

4. **Pratique** :
   ```
   "Donne-moi 3 exercices pour pratiquer les décorateurs, 
   du plus simple au plus complexe"
   ```

## Conclusion

FoyerGPT est conçu pour s'adapter à vos besoins. N'hésitez pas à :
- Expérimenter avec différents agents
- Affiner vos prompts systèmes
- Partager vos agents utiles avec la communauté
- Nous faire part de vos suggestions d'amélioration

Bon chat avec vos agents IA !