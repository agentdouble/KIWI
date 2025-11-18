#!/bin/bash

# Script pour lancer le backend et le frontend

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIN_NODE_VERSION="18.0.0"
NVMRC_PATH="$SCRIPT_DIR/.nvmrc"

load_nvm() {
    if command -v nvm >/dev/null 2>&1; then
        return 0
    fi

    if [ -s "$HOME/.nvm/nvm.sh" ]; then
        # shellcheck disable=SC1090
        . "$HOME/.nvm/nvm.sh"
        return 0
    fi

    if [ -s "$HOME/.config/nvm/nvm.sh" ]; then
        # shellcheck disable=SC1090
        . "$HOME/.config/nvm/nvm.sh"
        return 0
    fi

    if [ -s "/usr/local/opt/nvm/nvm.sh" ]; then
        # shellcheck disable=SC1090
        . "/usr/local/opt/nvm/nvm.sh"
        return 0
    fi

    return 1
}

version_ge() {
    local IFS=.
    local i ver_a=($1) ver_b=($2)

    for ((i=${#ver_a[@]}; i<3; i++)); do ver_a[i]=0; done
    for ((i=${#ver_b[@]}; i<3; i++)); do ver_b[i]=0; done

    for ((i=0; i<3; i++)); do
        if (( ver_a[i] > ver_b[i] )); then
            return 0
        elif (( ver_a[i] < ver_b[i] )); then
            return 1
        fi
    done

    return 0
}

get_env_value() {
    local var_name="$1"
    local file_path="$2"
    local value="${!var_name:-}"

    if [ -z "$value" ] && [ -f "$file_path" ]; then
        value=$(grep -E "^${var_name}=" "$file_path" | tail -n 1 | cut -d '=' -f2- | tr -d '\r')
    fi

    # Retirer les guillemets éventuels autour de la valeur
    value="${value%\"}"
    value="${value#\"}"

    echo "$value"
}

extract_port() {
    local url="$1"
    if [ -z "$url" ]; then
        echo ""
        return
    fi
    python3 - <<'PY' "$url"
from urllib.parse import urlparse
import sys

url = sys.argv[1]
if '://' not in url:
    url = 'http://' + url

parsed = urlparse(url)
port = parsed.port
if port is None:
    if parsed.scheme == 'https':
        port = 443
    elif parsed.scheme == 'http':
        port = 80
if port:
    print(port)
PY
}

free_port() {
    local port="$1"
    [ -z "$port" ] && return

    local pids
    pids=$(lsof -ti tcp:"$port" 2>/dev/null | tr '\n' ' ' | sed 's/ *$//')
    if [ -n "$pids" ]; then
        echo "🔌 Port $port occupé par PID(s): $pids — arrêt..."
        kill $pids 2>/dev/null
        sleep 1
        if lsof -ti tcp:"$port" >/dev/null 2>&1; then
            pids=$(lsof -ti tcp:"$port" 2>/dev/null | tr '\n' ' ' | sed 's/ *$//')
            if [ -n "$pids" ]; then
                echo "   Port $port toujours occupé, forçage (kill -9)..."
                kill -9 $pids 2>/dev/null
                sleep 1
            fi
        fi
    fi
}

BACKEND_ENV_FILE="$SCRIPT_DIR/backend/.env"
FRONTEND_ENV_FILE="$SCRIPT_DIR/frontend/.env"

BACKEND_URL=$(get_env_value "BACKEND_URL" "$BACKEND_ENV_FILE")
if [ -z "$BACKEND_URL" ]; then
    BACKEND_URL=$(get_env_value "VITE_BACKEND_URL" "$FRONTEND_ENV_FILE")
fi
[ -z "$BACKEND_URL" ] && BACKEND_URL="http://localhost:8077"

FRONTEND_URL=$(get_env_value "VITE_FRONTEND_URL" "$FRONTEND_ENV_FILE")
if [ -z "$FRONTEND_URL" ]; then
    FRONTEND_URL=$(get_env_value "FRONTEND_URL" "$BACKEND_ENV_FILE")
fi
[ -z "$FRONTEND_URL" ] && FRONTEND_URL="http://localhost:8091"

CORS_ORIGINS=$(get_env_value "CORS_ORIGINS" "$BACKEND_ENV_FILE")
[ -z "$CORS_ORIGINS" ] && CORS_ORIGINS="http://localhost:5173,http://localhost:5174,http://localhost:3000"

# Ajouter automatiquement les URLs frontend et backend, comme le backend le ferait
CORS_ORIGINS="$CORS_ORIGINS,$FRONTEND_URL,$BACKEND_URL"

ALLOWED_CORS_ORIGINS=()
IFS=',' read -r -a __raw_origins <<< "$CORS_ORIGINS"
for origin in "${__raw_origins[@]}"; do
    trimmed=$(echo "$origin" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    trimmed=${trimmed%/}
    if [ -n "$trimmed" ]; then
        case " ${ALLOWED_CORS_ORIGINS[*]} " in
            *" $trimmed "*) ;;
            *) ALLOWED_CORS_ORIGINS+=("$trimmed");;
        esac
    fi
done

unset __raw_origins

BACKEND_PORT=$(extract_port "$BACKEND_URL")
FRONTEND_PORT=$(extract_port "$FRONTEND_URL")

declare -a PORTS_TO_FREE=()
for port in "$BACKEND_PORT" "$FRONTEND_PORT"; do
    if [ -n "$port" ]; then
        case " ${PORTS_TO_FREE[*]} " in
            *" $port "*) ;;
            *) PORTS_TO_FREE+=("$port");;
        esac
    fi
done

echo "🚀 Démarrage des serveurs..."
echo ""

# Libérer les ports requis avant de démarrer
if [ ${#PORTS_TO_FREE[@]} -gt 0 ]; then
    echo "🧹 Vérification des ports requis..."
    for port in "${PORTS_TO_FREE[@]}"; do
        free_port "$port"
    done
fi

# Utiliser nvm si un .nvmrc est présent
if [ -f "$NVMRC_PATH" ]; then
    NVMRC_VERSION=$(tr -d ' \t\r\n' < "$NVMRC_PATH")
    if [ -n "$NVMRC_VERSION" ]; then
        if load_nvm && command -v nvm >/dev/null 2>&1; then
            echo "🔄 nvm use $NVMRC_VERSION (détecté via .nvmrc)"
            if ! nvm use "$NVMRC_VERSION" >/dev/null; then
                echo "⚠️  Impossible d'utiliser Node.js $NVMRC_VERSION via nvm. Installez-la avec 'nvm install $NVMRC_VERSION'."
            else
                NODE_VERSION_RAW=$(node -v 2>/dev/null)
            fi
        else
            echo "⚠️  .nvmrc détecté (version $NVMRC_VERSION) mais nvm n'est pas disponible. Chargez nvm dans votre shell puis relancez."
        fi
        MIN_NODE_VERSION="$NVMRC_VERSION"
    fi
fi

# Vérifier la version de Node.js pour éviter les erreurs Vite sur les environnements distants
if command -v node >/dev/null 2>&1; then
    NODE_VERSION_RAW=${NODE_VERSION_RAW:-$(node -v 2>/dev/null)}
    NODE_VERSION=${NODE_VERSION_RAW#v}
    if ! version_ge "$NODE_VERSION" "$MIN_NODE_VERSION"; then
        echo "❌ Node.js $NODE_VERSION_RAW détecté. Vite requiert la version $MIN_NODE_VERSION ou plus."
        if [ -f "$NVMRC_PATH" ]; then
            echo "   Exécutez 'nvm install $MIN_NODE_VERSION' puis relancez le script."
        else
            echo "   Merci de mettre à jour Node.js (ex: via nvm install 20 && nvm use 20) avant de relancer."
        fi
        exit 1
    fi
else
    echo "❌ Node.js introuvable. Installez Node.js >= $MIN_NODE_VERSION avant de démarrer le frontend."
    exit 1
fi

# Fonction pour tuer les processus à la fin
cleanup() {
    echo ""
    echo "⏹️  Arrêt des serveurs..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Capturer Ctrl+C pour arrêter proprement
trap cleanup INT

# Lancer le backend
echo "📦 Démarrage du backend..."
cd "$SCRIPT_DIR/backend" && uv run python run.py &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Attendre que le backend soit prêt
sleep 3

# Lancer le frontend
echo "🎨 Démarrage du frontend..."
cd "$SCRIPT_DIR/frontend" && npm run dev &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

echo ""
echo "✅ Serveurs démarrés:"
echo "   - Backend:  $BACKEND_URL"
echo "   - Frontend: $FRONTEND_URL"
if [ ${#ALLOWED_CORS_ORIGINS[@]} -gt 0 ]; then
    echo "   - CORS autorisés :"
    for origin in "${ALLOWED_CORS_ORIGINS[@]}"; do
        echo "       - $origin"
    done
fi
echo ""
echo "Appuyez sur Ctrl+C pour arrêter les serveurs"

# Attendre que les processus se terminent
wait $BACKEND_PID $FRONTEND_PID
