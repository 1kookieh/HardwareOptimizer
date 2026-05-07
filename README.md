# HardwareOptimizer

[![CI](https://github.com/1kookieh/HardwareOptimizer/actions/workflows/ci.yml/badge.svg)](https://github.com/1kookieh/HardwareOptimizer/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/UI-PySide6-41CD52?logo=qt&logoColor=white)
![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D4?logo=windows&logoColor=white)
![SQLite](https://img.shields.io/badge/Storage-SQLite-003B57?logo=sqlite&logoColor=white)
![pytest](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)
![Status](https://img.shields.io/badge/status-MVP%20ativo-2563EB)
![Safety](https://img.shields.io/badge/mode-advisory--first-22C55E)

HardwareOptimizer é um app desktop local-first para Windows que analisa hardware, Windows, BIOS/UEFI, drivers e atualizações para gerar recomendações explicáveis de otimização, estabilidade e segurança.

> O projeto é advisory-first: ele coleta evidências e orienta ações manuais, mas nunca altera BIOS/UEFI, registro, drivers, overclock, undervolt, voltagem, frequência, fan curve, plano de energia ou power limit automaticamente.

## Visão Geral

O app foi pensado para pessoas que querem entender o estado real do PC antes de mexer em configurações sensíveis. A coleta é local, read-only e sem UAC. As recomendações são determinísticas, priorizadas por perfil e acompanhadas de evidências, risco, confiança, passos manuais, validação e rollback quando aplicável.

Fluxo principal:

1. Escolha um perfil de análise.
2. Selecione jogos quando o perfil for Jogos.
3. Defina o objetivo da análise.
4. Inicie a coleta local.
5. Revise hardware, BIOS/UEFI, atualizações, jogos, histórico e recomendações.
6. Exporte um relatório JSON ou HTML.

## Funcionalidades

- UI desktop em PySide6 com tema dark/light, tela inicial premium, dashboard pós-análise, sidebar, cards de resumo e tabelas organizadas.
- Botão central de análise com cancelamento imediato pela UI: ao clicar em "PARAR", a interface volta para o estado pronto e ignora resultados tardios da coleta cancelada.
- Coleta read-only de sistema, CPU, RAM, GPU, storage, placa-mãe, BIOS/UEFI, TPM, Secure Boot, boot mode, virtualização, Hyper-V, VBS/HVCI, Fast Startup, hibernação, sensores opcionais e atualizações.
- Detecção de BIOS detalhada quando o fabricante expõe dados via WMI, incluindo Lenovo, HP e Dell.
- Enriquecimento online somente com fontes oficiais quando há fabricante reconhecido.
- Perfis de análise: Jogos, Desenvolvimento, Edição de Vídeo, Uso Geral, Alto Desempenho, Estabilidade e Baixo Consumo.
- Jogos suportados: Valorant, League of Legends, Call of Duty / Warzone, Marvel Rivals, Fortnite e Counter-Strike 2.
- Engine determinística de recomendações com guard ativo de segurança.
- Exportação de relatórios em JSON e HTML.
- Histórico local em SQLite.
- Logs locais com rotação em `%LOCALAPPDATA%/HardwareOptimizer/logs/app.log`.
- Testes automatizados com I/O externo mockado por padrão.

## Stack

| Área | Tecnologia |
| --- | --- |
| Linguagem | Python 3.11+ |
| Interface | PySide6 / Qt |
| Sistema operacional alvo | Windows 10/11 |
| Coleta local | `psutil`, WMI, PowerShell, COM Windows Update, registro em modo leitura |
| Persistência | SQLite |
| Relatórios | JSON e HTML |
| Testes | pytest |
| Lint e tipos | Ruff e mypy configurados em `pyproject.toml` |
| Build desktop | PyInstaller via `scripts/build.ps1` |
| CI | GitHub Actions |

## O Que É Detectado

| Área | Dados coletados | Método principal |
| --- | --- | --- |
| Sistema | SO, versão, build, arquitetura, hostname e plano de energia | `platform`, `socket`, `powercfg` |
| CPU | Nome, núcleos, threads, frequência e fabricante | `psutil`, WMI `Win32_Processor` |
| RAM | Total, uso, módulos, part number, clock configurado, speed nominal e form factor | `psutil`, WMI `Win32_PhysicalMemory` |
| GPU | Nome, driver, VRAM e Resizable BAR | WMI, `nvidia-smi`, PowerShell PnP |
| Placa-mãe | Fabricante e modelo | WMI `Win32_BaseBoard` |
| Storage | Partições, filesystem, uso e modo AHCI/RAID quando detectável | `psutil`, PowerShell, WMI |
| BIOS/UEFI | Fabricante, versão, data, Secure Boot, TPM, boot mode e virtualização | WMI, `Confirm-SecureBootUEFI`, `Get-Tpm`, `Get-ComputerInfo` |
| BIOS detalhada | Configurações expostas pelo fabricante | WMI Lenovo/HP/Dell quando disponível |
| Segurança | Hyper-V, VBS e HVCI/Memory Integrity | PowerShell e WMI Device Guard |
| Energia e boot | Fast Startup e hibernação | Registro Windows e `powercfg /a` |
| Sensores | Temperatura, clock e voltagem quando disponíveis | WMI `root\LibreHardwareMonitor` |
| Atualizações | Reboot pendente, último hotfix, updates disponíveis e drivers antigos | Registro, `Get-HotFix`, COM `Microsoft.Update.Session`, WMI |

Dados ausentes aparecem como "Não detectado automaticamente." Quando uma configuração de BIOS não é exposta ao Windows, o app trata isso como limitação real do firmware e não inventa estado.

## Recomendações

Cada recomendação pode incluir:

- título, categoria, prioridade, risco e confiança;
- justificativa e evidências usadas;
- estado atual e estado recomendado;
- benefício esperado sem promessa de ganho exato;
- impacto, quando não aplicar e nota de segurança;
- passos manuais, validação e rollback quando aplicável.

Categorias cobertas:

| Categoria | Exemplos | Risco típico |
| --- | --- | --- |
| BIOS/UEFI | XMP/EXPO/DOCP, Resizable BAR, modo RAID/AHCI, boost/PBO/Turbo, update de BIOS com cautela | `review` ou `risky` |
| Segurança | Secure Boot, TPM, VBS/HVCI como trade-off explícito | `safe` a `risky` |
| Windows | Plano de energia, apps em background, Fast Startup no perfil estabilidade | `safe` |
| Atualizações | Reinício pendente, Windows Update, hotfix antigo | `safe` |
| Drivers | GPU, chipset e drivers antigos com verificação manual no site oficial | `review` |
| Hardware | RAM insuficiente, armazenamento quase cheio e gargalos prováveis | `safe` ou `review` |
| Jogos | HAGS, anti-cheat, input lag, estabilidade e validação prática | `safe` ou `review` |

O padrão de qualidade das recomendações fica documentado em [`docs/recommendation_quality_spec.md`](docs/recommendation_quality_spec.md). A engine registra essa referência nos relatórios para auditoria.

## Interface

- Tela inicial com layout em três áreas: painel de análise, seleção de perfil/jogos/objetivo e resumo de segurança.
- Dashboard após análise com visão geral, maior ponto de atenção, próxima ação segura e principais prioridades.
- Abas para Hardware, Recomendações, BIOS/UEFI, Jogos, Atualizações e Histórico.
- Tabelas com cabeçalhos fixos, colunas organizadas e status de recomendação.
- Ícones locais em SVG para evitar dependência de CDN ou URLs externas.
- Assets opcionais de jogos em `app/ui/assets/games/` e ícones opcionais do orbit em `app/ui/assets/orbit/`.

Screenshots oficiais ainda não foram versionados. Quando capturados, devem ficar em `docs/screenshots/`.

## Instalação

Requisitos:

- Windows 10/11.
- Python 3.11+.

Runtime:

```powershell
py -m pip install -r requirements.txt
```

Desenvolvimento:

```powershell
py -m pip install -r requirements.txt -r requirements-dev.txt
```

O projeto não exige variáveis de ambiente obrigatórias para o MVP atual.

## Executar

```powershell
py -m app.main
```

## Validação

Suíte rápida, com I/O externo mockado por padrão:

```powershell
py -m pytest -q
```

Testes de integração, que podem tocar WMI, PowerShell, registro e HTTP reais:

```powershell
py -m pytest -m integration
```

Lint e typecheck:

```powershell
py -m ruff check .
py -m mypy app tests
```

No CI, Ruff e mypy existem como verificações não bloqueantes enquanto o baseline técnico evolui.

## Build

```powershell
.\scripts\build.ps1
.\scripts\build.ps1 -Clean
```

O executável é gerado em `dist/HardwareOptimizer/HardwareOptimizer.exe`.

Binários empacotados com PyInstaller podem receber alertas de reputação por antivírus. Para distribuição pública, o caminho recomendado é assinatura digital, documentação clara e distribuição por canal confiável, não desativar ferramentas de segurança.

## Estrutura

```text
app/
  collectors/       coleta read-only de sistema, hardware, BIOS, sensores e updates
  models/           dataclasses normalizadas
  recommendations/  engine determinística e regras por categoria
  reports/          exportação JSON/HTML
  safety/           ações bloqueadas e filtro ativo de segurança
  storage/          histórico local em SQLite
  ui/               interface PySide6, widgets e tokens visuais
docs/               especificações técnicas versionadas
scripts/            build e utilitários de manutenção
tests/              testes automatizados
```

Arquivos locais de instrução de agentes e design, como `AGENTS.md`, `CLAUDE.md` e `DESIGN.md`, podem existir no workspace, mas ficam fora dos commits por regra do projeto.

## Segurança e Privacidade

- Nenhuma alteração privilegiada é aplicada automaticamente.
- O app não coleta documentos pessoais, credenciais, tokens, histórico do navegador ou arquivos privados.
- O histórico fica em `%LOCALAPPDATA%/HardwareOptimizer/history.sqlite`.
- Não há telemetry, upload em nuvem ou envio de inventário de hardware para terceiros.
- Consultas online são limitadas a fontes oficiais quando o fabricante é reconhecido.
- O app não recomenda downgrade de BIOS.
- Update de BIOS só pode ser recomendado com modelo de placa-mãe e versão atual identificados.
- Recomendações de jogos não prometem ganho exato de FPS.

## Limitações Conhecidas

- BIOS/UEFI raramente expõe todas as configurações ao Windows.
- Sensores dependem do LibreHardwareMonitor expondo WMI.
- Windows Update COM pode demorar ou falhar por política corporativa.
- Estado "driver mais recente" exige confirmação em fonte oficial do fabricante.
- Caminhos exatos de menus de BIOS variam por fabricante/modelo e não são inventados.

## Status do Projeto

MVP ativo, com foco em qualidade de coleta, segurança das recomendações e evolução da interface. A licença declarada no `pyproject.toml` é proprietária; não há arquivo `LICENSE` público neste repositório no momento.

Próximos passos sugeridos:

- versionar screenshots reais em `docs/screenshots/`;
- separar `MainWindow` em controller e views menores;
- melhorar empty states e mensagens de erro;
- paralelizar consultas HTTP de fontes oficiais;
- expandir documentação de arquitetura e contribuição.
