export const short = {
  en_US: 'Shared long-term memory for AI agents, over MCP and a REST API.',
  es_ES:
    'Memoria compartida a largo plazo para agentes de IA, mediante MCP y una API REST.',
  de_DE:
    'Gemeinsames Langzeitgedächtnis für KI-Agenten über MCP und eine REST-API.',
  pl_PL: 'Wspólna pamięć długoterminowa dla agentów AI przez MCP i API REST.',
  fr_FR:
    'Mémoire partagée à long terme pour agents IA, via MCP et une API REST.',
}

export const long = {
  en_US:
    'Mnemosyne is a self-hosted long-term memory and second brain for AI agents. Hermes Agent, OpenClaw, Claude Code, Codex and any other MCP client can share one memory instead of each keeping its own.\n\n' +
    'The MCP endpoint (Streamable HTTP) and the REST API are served on one port. Every agent gets its own token, so each memory records which agent wrote it.\n\n' +
    'Recall combines vector search, full-text search and memory importance, using a built-in embedding model that runs offline on your server. Mnemosyne also keeps a knowledge graph with temporal facts, and memory banks to keep different subjects apart.\n\n' +
    'All data is stored on your server in SQLite. After installing, run "Add Agent Token" to create the first token and the connection URLs for your agent.',
  es_ES:
    'Mnemosyne es una memoria a largo plazo y un segundo cerebro autoalojados para agentes de IA. Hermes Agent, OpenClaw, Claude Code, Codex y cualquier otro cliente MCP pueden compartir una sola memoria en lugar de tener cada uno la suya.\n\n' +
    'El punto de acceso MCP (HTTP en streaming) y la API REST se sirven en un mismo puerto. Cada agente recibe su propio token, de modo que cada recuerdo registra qué agente lo escribió.\n\n' +
    'La recuperación combina búsqueda vectorial, búsqueda de texto completo e importancia del recuerdo, con un modelo de embeddings integrado que funciona sin conexión en su servidor. Mnemosyne también mantiene un grafo de conocimiento con hechos temporales y bancos de memoria para separar temas distintos.\n\n' +
    'Todos los datos se guardan en su servidor en SQLite. Tras la instalación, ejecute "Añadir token de agente" para crear el primer token y las URL de conexión de su agente.',
  de_DE:
    'Mnemosyne ist ein selbst gehostetes Langzeitgedächtnis und zweites Gehirn für KI-Agenten. Hermes Agent, OpenClaw, Claude Code, Codex und jeder andere MCP-Client können ein gemeinsames Gedächtnis nutzen, statt jeweils ein eigenes zu führen.\n\n' +
    'Der MCP-Endpunkt (Streamable HTTP) und die REST-API werden über denselben Port bereitgestellt. Jeder Agent erhält ein eigenes Token, sodass jede Erinnerung festhält, welcher Agent sie geschrieben hat.\n\n' +
    'Die Suche kombiniert Vektorsuche, Volltextsuche und die Wichtigkeit einer Erinnerung. Dazu dient ein integriertes Embedding-Modell, das offline auf Ihrem Server läuft. Mnemosyne führt außerdem einen Wissensgraphen mit zeitlichen Fakten und Gedächtnisbänke, um Themen voneinander zu trennen.\n\n' +
    'Alle Daten liegen in SQLite auf Ihrem Server. Führen Sie nach der Installation „Agent-Token hinzufügen“ aus, um das erste Token und die Verbindungs-URLs für Ihren Agenten zu erstellen.',
  pl_PL:
    'Mnemosyne to samodzielnie hostowana pamięć długoterminowa i drugi mózg dla agentów AI. Hermes Agent, OpenClaw, Claude Code, Codex i każdy inny klient MCP mogą korzystać ze wspólnej pamięci zamiast prowadzić własną.\n\n' +
    'Punkt końcowy MCP (Streamable HTTP) i API REST działają na jednym porcie. Każdy agent ma własny token, więc każde wspomnienie zapisuje, który agent je dodał.\n\n' +
    'Wyszukiwanie łączy wyszukiwanie wektorowe, pełnotekstowe i ważność wspomnienia, korzystając z wbudowanego modelu embeddingów działającego offline na Twoim serwerze. Mnemosyne prowadzi też graf wiedzy z faktami czasowymi oraz banki pamięci rozdzielające różne tematy.\n\n' +
    'Wszystkie dane są przechowywane na Twoim serwerze w SQLite. Po instalacji uruchom „Dodaj token agenta”, aby utworzyć pierwszy token i adresy połączenia dla agenta.',
  fr_FR:
    'Mnemosyne est une mémoire à long terme et un second cerveau auto-hébergés pour agents IA. Hermes Agent, OpenClaw, Claude Code, Codex et tout autre client MCP peuvent partager une seule mémoire au lieu d’en tenir chacun une.\n\n' +
    'Le point d’accès MCP (Streamable HTTP) et l’API REST sont servis sur un seul port. Chaque agent reçoit son propre jeton, si bien que chaque souvenir indique quel agent l’a écrit.\n\n' +
    'La recherche combine recherche vectorielle, recherche en texte intégral et importance du souvenir, grâce à un modèle d’embeddings intégré qui fonctionne hors ligne sur votre serveur. Mnemosyne tient aussi un graphe de connaissances avec des faits temporels, et des banques de mémoire pour séparer les sujets.\n\n' +
    'Toutes les données sont stockées sur votre serveur dans SQLite. Après l’installation, lancez « Ajouter un jeton d’agent » pour créer le premier jeton et les URL de connexion de votre agent.',
}
