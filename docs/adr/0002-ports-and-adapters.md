# ADR 0002: Ports and adapters for every external dependency
Status: accepted
Decision: `SourceFetcher`, `LLMClient`, `Notifier`, `Mailer` are protocols with a registry/factory. Domain code depends on the protocol only. Fake adapters back the test-suite so tests never hit the network.
Consequences: swapping Anthropic for another provider, or adding a WebSub/JSON source, touches only an adapter file.
