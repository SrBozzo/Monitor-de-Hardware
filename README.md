# 🖥️ Monitor de Hardware - Python Edition

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![OS](https://img.shields.io/badge/OS-Windows-success.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

Um painel de controle avançado e elegante para monitoramento de hardware no Windows, construído 100% em Python. Desenvolvido para entusiastas, gamers e desenvolvedores que precisam de telemetria precisa do sistema sem sobrecarregar a máquina.
---
## 📥 Download Direto (Pronto para Usar)

Não quer instalar o Python? Sem problemas! 
Baixe a versão compilada e rode diretamente no seu Windows:

👉 **[BAIXAR O EXECUTÁVEL (.exe) AQUI](https://github.com/SrBozzo/Monitor-de-Hardware/blob/main/Monitor_Hardware_SrBozzo.exe)**

*(Nota: Como a ferramenta vasculha os sensores do hardware, o Windows Defender pode exibir um aviso na primeira execução. Basta clicar em "Mais informações" > "Executar assim mesmo").*
---
## ✨ Funcionalidades Principais

* 📊 **Dashboard em Tempo Real:** Acompanhe o uso e a temperatura da CPU, RAM, GPU (NVIDIA), velocidade de leitura/gravação dos Discos e banda de Rede (Upload/Download) sem travamentos.
* 🎮 **Overlay Gamer:** Uma janela flutuante estilo *MSI Afterburner* (transparente e sem bordas) que sobrepõe jogos em modo "Janela Sem Bordas" para monitoramento sem risco de banimentos por Anti-Cheats.
* 🕵️ **Top Processos:** Um mini-gerenciador de tarefas integrado que lista os 5 programas que mais consomem recursos do PC.
* ⚙️ **Informações Detalhadas (WMI):** Leitura profunda de arquitetura do sistema, Placa-Mãe, BIOS, Periféricos conectados e lista de Drivers instalados no Kernel.
* 📄 **Exportação de Relatório:** Salve um relatório completo do estado do hardware em um arquivo de texto com um único clique.
---
## 👨‍💻 Para Desenvolvedores (Rodar pelo Código)

Se você quiser ver o código funcionando na sua IDE:

1. Clone este repositório:
```bash
git clone [https://github.com/SrBozzo/monitor-hardware.git](https://github.com/SrBozzo/monitor-hardware.git)
```
2. Instale as dependências necessárias:
```bash
pip install -r requirements.txt
```
3. Execute o programa:
```bash
python main.py
```
---
## 🛠️ Tecnologias Utilizadas

- **CustomTkinter:** Para uma Interface Gráfica (GUI) moderna e responsiva.

- **Psutil:** Para extração precisa de dados de sensores.

- **WMI:** Para leitura de dados estáticos profundos do Windows.

- **Multithreading:** Arquitetura de motor de dados em segundo plano.
---
### Autor
Criado por [SrBozzo](https://github.com/SrBozzo)
