# HardwareOptimizer

HardwareOptimizer é um app desktop local-first para Windows que analisa hardware, sistema, BIOS/UEFI, drivers e updates para gerar recomendações explicáveis de otimização, estabilidade e segurança.

> Importante: o app é advisory-first. Ele lê o máximo que o Windows, o firmware, ferramentas oficiais e fontes online oficiais expõem, mas nunca altera BIOS/UEFI, drivers, registro, overclock, undervolt, voltagem, frequência, fan curve ou power limit automaticamente.

## Status do MVP

- Interface desktop em PySide6 com tema dark/light e layout compacto.
- Coleta read-only em modo de detecção máxima, sem UAC, prompts ou mudanças no sistema.
- Coleta executada em thread separada (QThread) com barra de progresso por etapa: Sistema → Hardware → BIOS/UEFI → Atualizações locais → Fontes oficiais online. A janela permanece responsiva durante todo o processo.
- Leitura de configurações detalhadas de BIOS quando o fabricante expõe via WMI.
- Consulta de fontes oficiais online para Windows Update, drivers e suporte/BIOS.
- Engine determinística de recomendações por perfil.
- Exportação de relatório JSON/HTML.
- Histórico local em SQLite.
- Testes automatizados para modelos, coleta, recomendações, segurança, relatórios, storage, detecções e regressão de encoding.

## Screenshots

Os screenshots oficiais ainda não foram capturados.

- `docs/screenshots/dashboard.png` - Dashboard após análise.
- `docs/screenshots/recommendations.png` - Recomendações com risco/prioridade.
- `docs/screenshots/updates.png` - Aba de Atualizações.
- `docs/screenshots/bios.png` - Recomendações BIOS/UEFI.

## Perfis

| Perfil | Foco |
| --- | --- |
| Jogos | FPS consistente, input lag, compatibilidade com anti-cheat e estabilidade prática. |
| Desenvolvimento | WSL2, Docker, virtualização, estabilidade e produtividade. |
| Edição de Vídeo | GPU/driver, armazenamento, RAM e estabilidade em cargas longas. |
| Uso Geral | Recomendações equilibradas e de baixo risco. |
| Alto Desempenho | Energia, BIOS e Windows com foco em performance, sem OC automático. |
| Estabilidade | Updates, drivers, Fast Startup, armazenamento e configurações conservadoras. |
| Baixo Consumo | Menor consumo e menor ruído, preservando segurança. |

Jogos suportados no perfil Jogos: Valorant, League of Legends, Call of Duty / Warzone, Marvel Rivals, Fortnite e Counter-Strike 2.

## O que é detectado

| Área | Dados coletados | Método |
| --- | --- | --- |
| Sistema | SO, versão, build, arquitetura, hostname e plano de energia | `platform`, `socket`, `powercfg` |
| CPU | Nome, núcleos, threads, frequência e fabricante | `psutil`, WMI `Win32_Processor` |
| RAM | Total, uso, módulos, part number, clock configurado, speed nominal e form factor | `psutil`, WMI `Win32_PhysicalMemory` |
| GPU | Nome, driver, VRAM e Resizable BAR | WMI `Win32_VideoController`, `nvidia-smi`, PowerShell PnP |
| Placa-mãe | Fabricante e modelo | WMI `Win32_BaseBoard` |
| Armazenamento | Partições, filesystem, total/usado e modo AHCI/RAID quando detectável | `psutil`, PowerShell/WMI |
| BIOS/UEFI | Fabricante, versão, data, Secure Boot, TPM, TPM version, virtualização, boot mode | WMI, `Confirm-SecureBootUEFI`, `Get-Tpm`, `Get-ComputerInfo` |
| BIOS detalhada | Configurações expostas pelo fabricante, como Secure Boot, virtualization, boot, power e outros nomes publicados via WMI | Lenovo `root\wmi`, HP `root\hp\instrumentedBIOS`, Dell `root\dcim\sysman` |
| Firmware | Presença de tabelas Raw SMBIOS, ACPI e Firmware expostas ao Windows | `EnumSystemFirmwareTables` |
| Segurança/virtualização | Hyper-V, VBS e HVCI/Memory Integrity | `Get-WindowsOptionalFeature`, WMI `root\Microsoft\Windows\DeviceGuard` |
| Energia/boot | Fast Startup e hibernação | Registro Windows, `powercfg /a` |
| Sensores | Temperatura/clock/voltagem quando disponível | WMI `root\LibreHardwareMonitor` |
| Updates | Reboot pendente, último hotfix, updates disponíveis e drivers antigos | Registro, `Get-HotFix`, COM `Microsoft.Update.Session`, WMI `Win32_PnPSignedDriver` |

Dados ausentes aparecem como "Não detectado automaticamente." Quando a BIOS não publica uma configuração para o Windows, o app mostra "Não exposto pelo firmware ou pelo sistema operacional." Isso é intencional: o app não inventa estado de BIOS, sensor, driver ou compatibilidade.

### Fontes oficiais online

O enriquecimento online só usa páginas oficiais. Quando o fabricante da placa-mãe ou da BIOS é reconhecido (ASUS, Gigabyte, MSI, ASRock, Biostar, EVGA, Lenovo, Dell, HP, Acer, Samsung, LG, Intel, AMI, Phoenix, Insyde, Supermicro, NZXT), o app aponta para a página oficial de suporte do vendor. Se o vendor não é reconhecido, o campo `bios_lookup_url` permanece como "Não detectado automaticamente." O app nunca cai em buscador externo (Google/Bing) para evitar vazamento de modelo da placa-mãe a terceiros.

## O que é recomendado

| Categoria | Exemplos | Risco típico |
| --- | --- | --- |
| BIOS/UEFI | XMP/EXPO/DOCP, Resizable BAR, modo RAID/AHCI, boost/PBO/Turbo, update de BIOS com cautela | `review` ou `risky` |
| Segurança | Secure Boot, TPM, VBS/HVCI como trade-off explícito | `safe` a `risky` |
| Windows | Plano de energia, apps em background, Fast Startup no perfil estabilidade | `safe` |
| Updates | Reinício pendente, Windows Update, hotfix antigo | `safe` |
| Drivers | GPU e drivers antigos com verificação manual no site oficial | `review` |
| Hardware | RAM insuficiente, armazenamento quase cheio | `safe` ou `review` |
| Jogos | HAGS, anti-cheat, ajustes competitivos e validação prática | `safe` ou `review` |

Cada recomendação inclui título, categoria, prioridade, risco, justificativa, estado atual, estado recomendado, benefício esperado, impacto, quando não aplicar, validação, nota de segurança, passos manuais, evidência, rollback, confiança e confirmação manual quando necessário.

## Como funciona a checagem de updates e internet

A checagem é somente leitura:

- Reboot pendente: verifica chaves de registro conhecidas do Windows Update, Component Based Servicing e `PendingFileRenameOperations`.
- Último hotfix: usa `Get-HotFix`, ordena por data e calcula idade em dias.
- Updates disponíveis: usa COM `Microsoft.Update.Session` para contar updates de software não instalados. Pode demorar 30-60s e falhar em máquinas bloqueadas por política.
- Drivers antigos: consulta `Win32_PnPSignedDriver` e lista drivers relevantes com data acima de aproximadamente 3 anos.
- Fontes oficiais online: testa acesso a Microsoft Update Catalog, página oficial do Windows e páginas oficiais de driver conforme GPU detectada.
- BIOS/suporte: monta URL de busca para o fabricante/modelo detectado, sem baixar firmware nem executar atualização.

O app não baixa, instala, remove nem atualiza nada automaticamente.

## Instalação

Requisitos:

- Windows 10/11.
- Python 3.11+.

```powershell
py -m pip install -r requirements.txt
```

## Executar

```powershell
py -m app.main
```

## Testes

```powershell
py -m pytest -q
```

Comandos opcionais quando configurados:

```powershell
py -m ruff check .
py -m mypy app tests
```

## Empacotar

```powershell
.\scripts\build.ps1
.\scripts\build.ps1 -Clean
```

O executável é gerado em `dist/HardwareOptimizer/HardwareOptimizer.exe`.

Antivírus podem sinalizar binários PyInstaller por reputação. Não desabilite ferramentas de segurança; para distribuição pública, prefira assinatura digital e documentação clara.

## Relatórios e histórico

- JSON e HTML são exportados localmente pela UI.
- O histórico fica em `%LOCALAPPDATA%/HardwareOptimizer/history.sqlite`.
- Não há telemetry, upload em nuvem ou coleta de documentos pessoais.

## Estrutura

```text
app/
  collectors/       coleta read-only de sistema, hardware, BIOS, sensores e updates
  models/           dataclasses normalizadas
  recommendations/  engine determinística e regras por área
  reports/          exportação JSON/HTML
  safety/           ações bloqueadas e regras de segurança
  storage/          SQLite de histórico
  ui/               PySide6
tests/              testes automatizados
scripts/            build PyInstaller
CLAUDE.md           instruções originais do projeto
DESIGN.md           design system
```

## Limitações conhecidas

- BIOS/UEFI raramente expõe todos os estados para o Windows; o app lê interfaces públicas e WMI de fabricante quando existem, e marca o restante como não exposto.
- Caminhos exatos de menu de BIOS não são informados sem evidência de fabricante/modelo.
- Sensores dependem do LibreHardwareMonitor rodando e expondo WMI.
- Windows Update COM pode demorar ou falhar por política corporativa.
- Driver "mais recente" exige verificação no site oficial do fabricante; o app apenas identifica sinais de driver antigo.
- Recomendações de jogos não prometem ganho exato de FPS.
- Update de BIOS nunca é recomendado sem modelo exato da placa-mãe e versão atual identificados; downgrade nunca é recomendado.

## Regras de segurança

- Não aplicar alterações destrutivas ou privilegiadas automaticamente.
- Não recomendar desabilitar Secure Boot, TPM, firewall, antivírus ou proteções de memória como tweak genérico.
- Não automatizar BIOS/UEFI, OC/UV, voltagem, frequência, power limit, driver ou registro.
- Marcar incerteza como não detectada ou não exposta, sem fingir certeza.
- Preferir evidência, risco, confiança, validação e rollback a promessas de ganho.

## Fluxo de uso

1. Abra o app com `py -m app.main`.
2. Escolha um perfil.
3. Se usar o perfil Jogos, selecione os jogos relevantes.
4. Clique em "Analisar computador".
5. Revise as abas Hardware, Atualizações, BIOS/UEFI, Jogos e Recomendações.
6. Marque recomendações como pendentes, aplicadas ou ignoradas.
7. Exporte JSON/HTML se quiser guardar ou compartilhar o diagnóstico.
