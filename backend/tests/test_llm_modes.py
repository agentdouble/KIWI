#!/usr/bin/env python3
"""
Test des modes LLM (API et Local)
"""
import asyncio
import os
import sys
sys.path.append('.')

from app.config import settings
from app.services.llm_service import get_llm_service

async def test_llm_service():
    """Test le service LLM dans le mode configuré"""
    print(f"\n🧪 TEST DU SERVICE LLM")
    print(f"="*50)
    print(f"Mode actuel: {settings.llm_mode}")
    
    # Obtenir le service
    llm = get_llm_service()
    print(f"Service initialisé: {llm.__class__.__name__}")
    print(f"Mode du service: {llm.mode}")
    print(f"Modèle utilisé: {llm.model_name}")
    
    # Test 1: Génération simple
    print(f"\n📝 Test 1: Génération simple")
    messages = [
        {"role": "user", "content": "Dis bonjour en une phrase courte."}
    ]
    
    try:
        response = await llm.generate_response(messages)
        print(f"✅ Réponse: {response}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 2: Génération avec métadonnées
    print(f"\n📊 Test 2: Génération avec métadonnées")
    messages = [
        {"role": "system", "content": "Tu es un assistant utile."},
        {"role": "user", "content": "Compte de 1 à 5."}
    ]
    
    try:
        response, metadata = await llm.generate_response_with_metadata(messages)
        print(f"✅ Réponse: {response}")
        print(f"📈 Métadonnées:")
        for key, value in metadata.items():
            print(f"   - {key}: {value}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 3: Streaming (si supporté)
    print(f"\n🌊 Test 3: Streaming")
    messages = [
        {"role": "user", "content": "Raconte une très courte histoire en 2 phrases."}
    ]
    
    try:
        print(f"Réponse en streaming: ", end="", flush=True)
        async for chunk in llm.generate_stream_response(messages):
            print(chunk, end="", flush=True)
        print("\n✅ Streaming terminé")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
    
    # Test 4: Health check (si mode local)
    if llm.is_local_mode:
        print(f"\n🏥 Test 4: Health Check")
        try:
            is_healthy = await llm.health_check()
            print(f"{'✅' if is_healthy else '❌'} Serveur vLLM: {'En ligne' if is_healthy else 'Hors ligne'}")
        except Exception as e:
            print(f"❌ Erreur health check: {e}")

async def test_mode_switching():
    """Test le changement de mode"""
    print(f"\n\n🔄 TEST DE CHANGEMENT DE MODE")
    print(f"="*50)
    
    current_mode = os.getenv("LLM_MODE", "api")
    print(f"Mode actuel dans l'environnement: {current_mode}")
    
    # Pour vraiment tester le changement, il faudrait:
    # 1. Modifier LLM_MODE dans l'environnement
    # 2. Recharger la configuration
    # 3. Réinitialiser le service
    
    print(f"⚠️  Note: Le changement de mode nécessite un redémarrage de l'application")
    print(f"   Pour tester l'autre mode:")
    print(f"   1. Modifier LLM_MODE dans .env")
    print(f"   2. Relancer ce script")

if __name__ == "__main__":
    print(f"🚀 Test des modes LLM")
    print(f"="*70)
    
    # Afficher la configuration
    print(f"\n📋 Configuration actuelle:")
    print(f"   LLM_MODE: {settings.llm_mode}")
    
    if settings.is_api_mode:
        print(f"   Mode: API (OpenAI-compatible HTTP API)")
        print(f"   API URL: {settings.api_url}")
        print(f"   Modèle: {settings.api_model}")
        print(f"   API Key: {'✅ Configurée' if settings.api_key else '❌ Manquante'}")
    else:
        print(f"   Mode: LOCAL (vLLM)")
        print(f"   URL: {settings.vllm_api_url}")
        print(f"   Modèle: {settings.vllm_model_name}")
        print(f"   Max Tokens: {settings.vllm_max_tokens}")
    
    # Lancer les tests
    asyncio.run(test_llm_service())
    asyncio.run(test_mode_switching())
    
    print(f"\n✅ Tests terminés")
