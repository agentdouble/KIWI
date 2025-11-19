# Configuration de l'API LLM (OpenAI-compatible)

## Étapes pour obtenir et configurer votre clé API :

### 1. Obtenir une clé API (exemple : Mistral)

1. Allez sur [console.mistral.ai](https://console.mistral.ai/)
2. Créez un compte ou connectez-vous
3. Dans la section "API Keys", créez une nouvelle clé
4. Copiez la clé (elle commence par `sk-`)

### 2. Configurer la clé dans le projet

Modifiez le fichier `.env` et remplacez `your_api_key_here` par votre vraie clé :

```bash
# Option 1 : Éditer manuellement le fichier .env
nano .env
# ou
vim .env

# Option 2 : Remplacer directement (remplacez sk-xxxxx par votre clé)
sed -i '' 's/your_api_key_here/sk-votre-vraie-cle-ici/' .env

# Option 3 : Écraser la ligne (remplacez sk-xxxxx par votre clé)
echo "API_KEY=sk-votre-vraie-cle-ici" > temp.env
grep -v API_KEY .env >> temp.env
mv temp.env .env
```

### 3. Vérifier la configuration

```bash
# Tester la connexion
uv run python main.py test
```

Si le test réussit, vous verrez :
```
✓ API key found
✓ Using model: mistral-small-latest
✓ Successfully connected to LLM API

Ready to generate presentations!
```

### 4. Première conversion

```bash
# Tester avec l'exemple fourni
uv run python main.py convert -i examples/sample_text.txt

# Ou avec votre propre texte
uv run python main.py convert -t "Créez une présentation sur l'intelligence artificielle"
```

## Sécurité

- **Ne jamais** committer le fichier `.env` avec votre vraie clé
- Le fichier `.gitignore` est déjà configuré pour ignorer `.env`
- Pour partager le projet, utilisez `.env.example` avec des valeurs factices

## Dépannage

### Erreur 401 Unauthorized
- Vérifiez que la clé est correcte (commence par `sk-`)
- Assurez-vous qu'il n'y a pas d'espaces avant/après la clé
- Vérifiez que votre compte Mistral a des crédits disponibles

### Erreur de connexion
- Vérifiez votre connexion internet
- Essayez avec un VPN si Mistral est bloqué dans votre région

### Pour voir la clé configurée (masquée)
```bash
# Affiche les premiers caractères seulement
grep API_KEY .env | sed 's/=.*$/=sk-****.../'
```
