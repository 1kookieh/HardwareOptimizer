# Recommendation Quality Spec

Esta spec define o padrão de qualidade das recomendações do HardwareOptimizer.
Ela deve orientar regras determinísticas, textos de UI, relatórios e futuras revisões técnicas.

O app é advisory-first: ele lê dados locais e fontes oficiais quando disponíveis, explica achados e orienta ações. Ele nunca aplica BIOS/UEFI, overclock, undervolt, voltagem, frequência, power limit, drivers, registro ou mudanças destrutivas automaticamente.

## Objetivo

Transformar recomendações genéricas em recomendações específicas, evidenciadas, seguras e compreensíveis para pessoas comuns, mantendo precisão técnica para usuários avançados.

Uma recomendação boa deve responder:

1. O que foi detectado.
2. Por que isso importa.
3. O que fazer.
4. Qual impacto pode ser esperado.
5. Qual risco existe.
6. Qual é a confiança.
7. Qual evidência sustenta a orientação.
8. Quais dados estão ausentes ou não expostos.
9. Como validar e, quando possível, como reverter.

## Princípios

- Nunca fingir certeza.
- Separar fato detectado, inferência e dado ausente.
- Usar linguagem PT-BR clara, curta e profissional.
- Preferir fontes oficiais.
- Bloquear ou rebaixar recomendações quando faltar dado essencial.
- Não prometer FPS, estabilidade ou desempenho garantido.
- Não recomendar ajuste sensível como padrão universal.
- Não gerar recomendação só para aumentar quantidade.

## Campos obrigatórios por recomendação

- Título curto.
- Categoria.
- Prioridade.
- Risco.
- Confiança.
- Estado atual.
- Estado recomendado.
- Justificativa.
- Benefício esperado conservador.
- Impacto ou trade-off.
- Quando não aplicar.
- Como validar.
- Nota de segurança.
- Evidências.
- Rollback quando aplicável.

## Risco

### safe

Baixo risco e adequado para usuário comum.

Exemplos:

- Reiniciar para concluir updates.
- Instalar update oficial do Windows.
- Verificar apps de inicialização.
- Liberar espaço em disco por ferramenta nativa.

### review

Exige leitura, acompanhamento ou decisão consciente.

Exemplos:

- Atualizar driver manualmente pelo fabricante.
- Ativar XMP/EXPO.
- Revisar Resizable BAR.
- Ajustar plano de energia avançado.

### risky

Pode causar instabilidade, perda de acesso, redução de segurança ou falha de boot.

Exemplos:

- Alterar AHCI/RAID.
- Desativar proteção de memória.
- Alterar boot mode.
- Mexer em overclock, undervolt ou tensão.

### blocked

Não deve ser apresentado como ação executável.

Use quando:

- faltar dado essencial;
- não houver fonte oficial;
- houver risco alto demais;
- a compatibilidade não puder ser confirmada;
- a ação depender de diagnóstico técnico presencial.

## Confiança

### high

Use quando há evidência direta, precisa e com baixo risco de falso positivo.

### medium

Use quando há evidência parcial ou indício forte, mas a decisão depende de contexto.

### low

Use quando faltam dados importantes ou a inferência é fraca.

## Prioridade

### critical

Risco de segurança, falha, perda de dados ou incompatibilidade importante.

### high

Provável melhora de estabilidade, compatibilidade, segurança ou funcionamento essencial.

### medium

Pode melhorar experiência, desempenho ou manutenção, mas não é urgente.

### low

Opcional, situacional ou de impacto pequeno.

## Regras proibidas

- Inventar hardware, BIOS, driver, versão, update ou FPS.
- Recomendar update de BIOS sem modelo exato e versão atual.
- Recomendar BIOS sem fonte oficial do fabricante.
- Dizer que a BIOS ideal é sempre a mais recente.
- Recomendar downgrade de BIOS.
- Prometer ganho exato de FPS.
- Recomendar driver updater genérico.
- Recomendar download fora de fonte oficial.
- Recomendar desativar Secure Boot, TPM, firewall, antivírus ou proteções de memória como tweak genérico.
- Recomendar overclock, undervolt, voltagem ou power limit como seguro para todos.
- Tratar ausência de dado como problema confirmado.

## BIOS/UEFI

BIOS/UEFI é sempre área sensível.

Para recomendar update de BIOS é necessário:

- fabricante;
- modelo exato;
- revisão da placa quando aplicável;
- versão atual da BIOS;
- data da BIOS;
- CPU instalada;
- fonte oficial do fabricante;
- motivo técnico ou changelog relevante;
- aviso sobre energia estável e backup.

Se faltar dado essencial, a orientação deve ser bloqueada ou limitada a “não há dados suficientes para recomendar update”.

## Drivers

Recomendações de driver devem:

- citar dispositivo, fabricante, versão e data quando detectados;
- priorizar GPU, chipset, rede, áudio e armazenamento;
- apontar fonte oficial;
- diferenciar driver ausente, antigo e apenas opcional;
- evitar “atualize tudo”.

## Windows e updates

Recomendações devem:

- separar update crítico, recomendado e opcional;
- explicar reinicialização pendente;
- preferir ferramentas nativas;
- evitar limpeza agressiva;
- nunca reduzir segurança sem trade-off explícito.

## Jogos

Recomendações para jogos devem:

- não prometer FPS;
- priorizar estabilidade antes de desempenho;
- considerar GPU, CPU, RAM, SSD/HDD, driver, temperatura e overlays;
- diferenciar ajuste global de ajuste por jogo;
- explicar como validar em jogo real.

## Hardware

Recomendações de upgrade devem:

- depender de evidência;
- separar necessário, recomendado e opcional;
- considerar compatibilidade física, elétrica e térmica;
- evitar culpar hardware sem diagnóstico.

## Texto para usuário comum

Use:

- frases curtas;
- tom profissional;
- explicação simples do motivo;
- alerta sem assustar;
- ação prática.

Evite:

- jargão sem explicação;
- “garantido”;
- “100% seguro”;
- “aumenta FPS” sem medição;
- linguagem alarmista;
- marketing exagerado.

## Checklist de aceite

Antes de aceitar uma regra nova:

- A recomendação cita evidência real ou dado ausente.
- A ação é compatível com o risco.
- A confiança reflete a qualidade da evidência.
- Há validação prática.
- Há rollback quando aplicável.
- Não há promessa de ganho exato.
- Não há fonte não oficial para BIOS, firmware ou driver.
- O texto é compreensível para pessoa comum.
- A recomendação passa pelos guards de segurança do app.

## Integração com o código

O código deve referenciar este arquivo como contrato de qualidade por meio de `app/recommendations/quality_spec.py`.
Relatórios e logs podem registrar caminho e hash da spec para auditoria.
