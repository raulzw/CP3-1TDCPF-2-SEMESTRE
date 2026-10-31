# Exercício 1.3 — Decisões de arquitetura com o Teorema CAP

| # | Cenário | CP/AP | Justificativa |
|---|---------|-------|---------------|
| 1 | Saldo bancário de clientes | **CP** | Dois nós mostrando saldos diferentes permitem gasto duplo. É melhor recusar a operação durante uma partição do que aceitar um saldo inconsistente. |
| 2 | Ingestão de 500 mil eventos de firewall/min num SOC | **AP** | Parar de aceitar logs durante um ataque é pior do que ter consistência eventual. Os eventos podem ser reconciliados depois; o que não pode é perdê-los. |
| 3 | Cache de tokens de sessão | **AP** | O cache precisa responder sempre e rápido; um token desatualizado por alguns segundos é aceitável. Exceção: sessões críticas (admin, revogação de token) pedem CP, pois um token revogado não pode continuar válido. |
| 4 | Registro de quem autorizou cada transferência (auditoria) | **CP** | A trilha de auditoria precisa ser exata e não pode divergir entre nós, pois tem valor legal. Prefere-se negar a escrita a gravar um registro inconsistente. |
| 5 | Feed de IOCs replicado em 5 regiões | **AP** | Cada região precisa continuar consultando o feed mesmo isolada; um IOC chegar alguns segundos depois em uma região é tolerável. Indisponibilidade deixaria a região sem proteção. |
