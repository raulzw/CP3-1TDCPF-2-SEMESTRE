"""Exercício 13.1 — Chatbot de segurança de linha de comando, com histórico da conversa."""
from llm import ErroLLM, chat, usando_mock

SISTEMA = ("Você é um analista de segurança sênior e didático. Responda em português, em no máximo "
           "4 frases. Recuse ajudar a atacar sistemas de terceiros.")
MAX_MENSAGENS_HISTORICO = 20  # limita custo/tokens: mantém só as últimas trocas


def main():
    historico = [{"role": "system", "content": SISTEMA}]
    if usando_mock():
        print("(sem OPENAI_API_KEY — usando LLM simulado)")
    print("Chatbot de Segurança. Digite /sair para encerrar.")
    while True:
        try:
            pergunta = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            pergunta = "/sair"
        if not pergunta:
            continue
        if pergunta.lower() == "/sair":
            print("Assistente: Até logo!")
            break

        historico.append({"role": "user", "content": pergunta})
        try:
            resposta = chat(historico, temperature=0.5)
        except ErroLLM as e:
            historico.pop()  # não guarda pergunta sem resposta
            print(f"Assistente: [erro ao falar com a API: {e}] Tente novamente.")
            continue
        historico.append({"role": "assistant", "content": resposta})
        historico[1:] = historico[1:][-MAX_MENSAGENS_HISTORICO:]
        print(f"Assistente: {resposta}")


if __name__ == "__main__":
    main()
