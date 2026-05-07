# 1kookieh

> Sugestão de README para o perfil GitHub. Como o repositório `1kookieh/1kookieh` não está neste workspace, este arquivo pode ser usado como base para o `README.md` do perfil.

Desenvolvedor focado em ferramentas desktop, automação para Windows e aplicações local-first com atenção a segurança, clareza de interface e validação técnica.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-Qt-41CD52?logo=qt&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-local%20storage-003B57?logo=sqlite&logoColor=white)
![PowerShell](https://img.shields.io/badge/PowerShell-Windows%20automation-5391FE?logo=powershell&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-tests-0A9EDC?logo=pytest&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-CI-2088FF?logo=githubactions&logoColor=white)

## Foco Atual

- Apps desktop locais para Windows.
- Coleta read-only de dados do sistema.
- UI em Python com PySide6/Qt.
- Recomendações técnicas explicáveis e seguras.
- Testes automatizados, CI e documentação de projeto.

## Projeto em Destaque

### [HardwareOptimizer](https://github.com/1kookieh/HardwareOptimizer)

App desktop local-first para Windows que analisa hardware, Windows, BIOS/UEFI, drivers e atualizações para gerar recomendações explicáveis de otimização, estabilidade e segurança.

**Stack:** Python 3.11+, PySide6, SQLite, WMI, PowerShell, pytest, Ruff, mypy e GitHub Actions.

**Destaques técnicos:**

- coleta local e read-only, sem UAC;
- engine determinística de recomendações com risco, confiança e evidências;
- UI desktop com tema dark/light e fluxo de análise guiado;
- histórico local em SQLite;
- exportação JSON/HTML;
- suíte de testes automatizados e workflow de CI.

## Como Trabalho

- Segurança primeiro: nenhuma ação sensível deve ser automatizada sem controle explícito.
- Documentação clara: comandos, limitações e comportamento real precisam estar visíveis.
- Interface útil: produto técnico também precisa ser compreensível para pessoas comuns.
- Validação contínua: testes e revisão antes de entregar mudanças.

## Stack Principal

| Área | Tecnologias |
| --- | --- |
| Linguagem | Python |
| Desktop UI | PySide6 / Qt |
| Windows | PowerShell, WMI, APIs locais em modo leitura |
| Dados locais | SQLite |
| Qualidade | pytest, Ruff, mypy |
| CI/CD | GitHub Actions |

## Em Evolução

Atualmente o foco está em amadurecer o HardwareOptimizer como produto desktop real: interface mais profissional, recomendações mais específicas, documentação melhor e validações automatizadas mais fortes.
