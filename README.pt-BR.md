<!--
  Links para arquivos fora de templates/, LICENSE e VERSION são absolutos de
  propósito: o espelho do CI/CD Catalog (catalog-mirror/) sincroniza este README
  sem esses arquivos, e links relativos quebram na página do catálogo.

  Todo título de seção começa com um ícone, e a âncora então começa com um
  hífen: "## 🔧 Inputs" vira #-inputs. Duas regras mantêm essas âncoras iguais
  no GitHub e na página do catálogo do GitLab. Use ícones de um caractere só:
  um que carrega seletor de variação (U+FE0F, como o sinal de aviso) deixa um
  caractere invisível na âncora. E não use "&" em título: ele vira hífen duplo
  no GitHub e simples no GitLab.
-->
<div align="left">
  <img src="https://raw.githubusercontent.com/Tooark/template-security-scanner/main/media/banner-ci-security-scanner.pt-BR.png" alt="CI Security Scanner" width="100%" />
</div>

# CI Security Scanner — templates de CI/CD do GitLab

Templates de CI/CD do GitLab que rodam a imagem
[`security-scanner`](https://github.com/Tooark/base-images/tree/main/security-scanner)
da Tooark — **Trivy** (vulnerabilidades), **Hadolint** (lint de Dockerfile) e
**Betterleaks** (detecção de secrets) sob um único CLI `ark-tools`, produzindo
um relatório `ark-report-tools v1.3`.

São sete templates em [`templates/`](templates/), um job cada. Inclua um, passe
os inputs, e o pipeline ganha o scan, os gates de falha, o banco de
vulnerabilidades em cache e os relatórios como artifacts do job. Funcionam via
`include: remote:` a partir de qualquer instância do GitLab, ou como componentes
de um CI/CD Catalog.

> **Usa GitHub Actions?** Os mesmos scans são distribuídos como uma GitHub
> Action em
> [`Tooark/action-security-scanner`](https://github.com/Tooark/action-security-scanner).
> Os inputs de lá têm os mesmos nomes em kebab-case: `trivy_severity` aqui é
> `trivy-severity` lá.

Novo em pipelines? O
[guia de onboarding](https://tooark.com/template-security-scanner/) percorre
cada arquivo deste repositório e o porquê de cada decisão, escrito para quem
conhece desenvolvimento de software, mas não CI. Fonte em
[`docs/`](https://github.com/Tooark/template-security-scanner/tree/main/docs).

🌍 **Idiomas:** [![USA Flag](https://flagcdn.com/w20/us.png) English](https://github.com/Tooark/template-security-scanner/blob/main/README.md) · ![Brazil Flag](https://flagcdn.com/w20/br.png) **Português (este arquivo)**

---

## 📑 Sumário

- [🚀 Início rápido](#-início-rápido)
- [📋 Requisitos](#-requisitos)
- [🧩 Templates](#-templates)
- [🚦 Gates de falha](#-gates-de-falha)
- [🔧 Inputs](#-inputs)
- [📊 Relatórios](#-relatórios)
- [🔀 Como funciona a precedência](#-como-funciona-a-precedência)
- [🔑 Secrets](#-secrets)
- [🍳 Receitas](#-receitas)
- [🔩 Sobrescrevendo o que os inputs não expõem](#-sobrescrevendo-o-que-os-inputs-não-expõem)
- [💾 Cache do banco do Trivy](#-cache-do-banco-do-trivy)
- [🐳 Qual imagem gerou o relatório](#-qual-imagem-gerou-o-relatório)
- [🔐 Notas de segurança](#-notas-de-segurança)
- [🔖 Versionamento](#-versionamento)
- [📦 Publicação](#-publicação)
- [🚧 Armadilhas](#-armadilhas)
- [📁 Estrutura do repositório](#-estrutura-do-repositório)
- [🧪 Desenvolvimento](#-desenvolvimento)
- [🔗 Projetos relacionados](#-projetos-relacionados)
- [🤝 Contribuição](#-contribuição)
- [🆘 Ajuda e Segurança](#-ajuda-e-segurança)
- [💖 Apoie](#-apoie)
- [📝 Licença](#-licença)

---

## 🚀 Início rápido

### Remote include

Funciona no gitlab.com e em qualquer instância que alcance
`raw.githubusercontent.com`. Não precisa de catálogo.

```yaml
include:
  - remote: "https://raw.githubusercontent.com/Tooark/template-security-scanner/v1.3.0/templates/full-scan.yml"
```

Esse único include adiciona um job `security:full-scan` ao stage `test`. Sem
inputs ele roda sem a etapa de imagem: Trivy no código-fonte, Betterleaks no
history do git e Hadolint no `./Dockerfile`. O job falha quando um
[gate](#-gates-de-falha) dispara, e os relatórios ficam guardados como artifacts
nos dois casos.

Para incluir a imagem que o pipeline construiu:

```yaml
include:
  - remote: "https://raw.githubusercontent.com/Tooark/template-security-scanner/v1.3.0/templates/full-scan.yml"
    inputs:
      stage: test
      image: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
      trivy_severity: "CRITICAL,HIGH"
      hadolint_failure_level: "warning"
```

### CI/CD Catalog

O catálogo só lista componentes hospedados na própria instância do GitLab.
Depois que o
[projeto-espelho](https://github.com/Tooark/template-security-scanner/tree/main/catalog-mirror)
publicar uma versão na sua:

```yaml
include:
  - component: $CI_SERVER_FQDN/tooark/ci-security-scanner/full-scan@1.3.0
    inputs:
      image: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
      trivy_severity: "CRITICAL,HIGH"
```

Pipelines completos, prontos para copiar, ficam em
[`examples/`](https://github.com/Tooark/template-security-scanner/tree/main/examples):

| Exemplo                                                                                                                                     | O que mostra                                                                         |
| ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| [`quick-start.gitlab-ci.yml`](https://github.com/Tooark/template-security-scanner/blob/main/examples/quick-start.gitlab-ci.yml)             | O include de uma linha acima                                                         |
| [`remote-include.gitlab-ci.yml`](https://github.com/Tooark/template-security-scanner/blob/main/examples/remote-include.gitlab-ci.yml)       | Build, scan completo da imagem enviada, um job de merge request e um override de job |
| [`catalog-component.gitlab-ci.yml`](https://github.com/Tooark/template-security-scanner/blob/main/examples/catalog-component.gitlab-ci.yml) | Os mesmos scans como componentes de catálogo, com rules e tags de runner             |

---

## 📋 Requisitos

| Requisito | Detalhe                                                                                                                                             |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| GitLab    | **16.11 ou mais novo**, gitlab.com ou self-managed; 17.0 ou mais novo para consumir de um CI/CD Catalog                                             |
| Runner    | Um executor que rode o job dentro da imagem: `docker`, `docker+machine` ou `kubernetes`. Não `shell` nem `ssh`                                      |
| Stage     | O stage indicado em `stage` (default `test`) precisa existir no pipeline                                                                            |
| Rede      | `ghcr.io` para a imagem do scanner, o banco de vulnerabilidades do Trivy (ou um `trivy_server`) e `raw.githubusercontent.com` para o remote include |

A matriz completa de suporte está em
[`SUPPORTED-INTEGRATIONS.md`](https://github.com/Tooark/template-security-scanner/blob/main/SUPPORTED-INTEGRATIONS.md).

---

## 🧩 Templates

Cada template gera exatamente um job, chamado `security:<template>`, que roda o
comando de mesmo nome do `ark-tools` dentro da imagem.

| Template                                               | Ferramenta  | O que faz                                                       | Input principal       |
| ------------------------------------------------------ | ----------- | --------------------------------------------------------------- | --------------------- |
| [`full-scan.yml`](templates/full-scan.yml)             | as três     | Imagem + código + secrets + lint de Dockerfile, relatório único | `image`, `scan_path`  |
| [`image-scan.yml`](templates/image-scan.yml)           | Trivy       | Scan de vulnerabilidades de uma imagem                          | `image` (obrigatório) |
| [`filesystem-scan.yml`](templates/filesystem-scan.yml) | Trivy       | Scan do código-fonte (lockfiles, pacotes de SO e de linguagem)  | `path`                |
| [`config-scan.yml`](templates/config-scan.yml)         | Trivy       | Scan de IaC / misconfiguration                                  | `path`                |
| [`repo-scan.yml`](templates/repo-scan.yml)             | Trivy       | Scan de repositório; aceita URL remota                          | `target`              |
| [`dockerfile-lint.yml`](templates/dockerfile-lint.yml) | Hadolint    | Lint de um Dockerfile                                           | `dockerfile`          |
| [`secret-scan.yml`](templates/secret-scan.yml)         | Betterleaks | Secrets no working tree e no history do git                     | `path`, `no_git`      |

O `full-scan` sem `image` pula a etapa de imagem; as outras etapas podem ser
desligadas com `skip_lint` e `skip_secrets`.

---

## 🚦 Gates de falha

Um gate disparado falha o job, e com ele o pipeline.

| Ferramenta  | Falha quando                                                              | Desligue com                            |
| ----------- | ------------------------------------------------------------------------- | --------------------------------------- |
| Trivy       | Uma severidade de `trivy_severity_fail` é encontrada e tem fix disponível | `trivy_exit_code: "0"`                  |
| Hadolint    | Há finding no nível `hadolint_failure_level` ou acima                     | `hadolint_failure_level: "none"`        |
| Betterleaks | Qualquer secret é detectado                                               | `betterleaks_fail_on_findings: "false"` |

O relatório e o gate são ajustes separados: `trivy_severity` decide o que entra
no relatório, `trivy_severity_fail` o que falha o job. A mesma separação vale
para `trivy_ignore_unfixed` e `trivy_ignore_unfixed_fail`.

O `allow_failure: true` mantém todos os gates, mas deixa o pipeline continuar:
o job termina com um aviso em vez de uma falha.

---

## 🔧 Inputs

Todo input é opcional, exceto `image` no `image-scan`. O bloco `spec:inputs` no
topo de cada template é a referência oficial, com a descrição e os valores
aceitos de cada input.

Atenção aos tipos: o GitLab rejeita um include cujo valor tenha o tipo errado.
`allow_failure` e `sbom` são **booleanos** e recebem um `true` sem aspas;
`rules` e `tags` são **arrays**; todo o resto é **string**, então os
liga/desliga entre eles recebem `"true"` ou `"false"` com aspas.

### O job

Em todos os templates.

| Input                 | Default                           | Notas                                                              |
| --------------------- | --------------------------------- | ------------------------------------------------------------------ |
| `job_name`            | `security:<template>`             | Troque para incluir o mesmo template mais de uma vez               |
| `stage`               | `test`                            | O stage precisa existir no pipeline                                |
| `rules`               | `[{when: on_success}]`            | Substitua para controlar quando o scan roda                        |
| `tags`                | `[]`                              | Tags de runner; vazio significa qualquer runner                    |
| `timeout`             | `1h`                              | `15m` no `dockerfile-lint`                                         |
| `allow_failure`       | `false`                           | Deixa o pipeline continuar quando um gate dispara                  |
| `reports_dir`         | `scan-reports`                    | Onde os relatórios são gravados, relativo ao diretório do projeto  |
| `artifacts_expire_in` | `7 days`                          | Por quanto tempo os artifacts dos relatórios são mantidos          |
| `scanner_image`       | `ghcr.io/tooark/security-scanner` | Troque para baixar de um mirror                                    |
| `scanner_version`     | `1.10`                            | Tag da imagem. Pine; `latest` torna os pipelines não reproduzíveis |
| `extra_args`          | —                                 | Flags extras repassadas à ferramenta depois do `--`                |

### O que escanear

| Input          | Default                      | Templates                                       | Notas                                                                                          |
| -------------- | ---------------------------- | ----------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `image`        | —                            | `full-scan`, `image-scan`                       | Referência da imagem. Vazio pula a etapa de imagem do `full-scan`; obrigatório no `image-scan` |
| `scan_path`    | `$CI_PROJECT_DIR`            | `full-scan`                                     | Path do projeto escaneado em busca de vulnerabilidades, secrets e Dockerfiles                  |
| `path`         | `$CI_PROJECT_DIR`            | `filesystem-scan`, `config-scan`, `secret-scan` | Diretório a escanear                                                                           |
| `target`       | `$CI_PROJECT_DIR`            | `repo-scan`                                     | Path local ou URL de repositório remoto                                                        |
| `dockerfile`   | `$CI_PROJECT_DIR/Dockerfile` | `dockerfile-lint`                               | O Dockerfile a ser analisado                                                                   |
| `dockerfiles`  | `Dockerfile`                 | `full-scan`                                     | Dockerfiles separados por vírgula, relativos a `scan_path`                                     |
| `scan_mode`    | `fs`                         | `full-scan`                                     | Modo do scan de código do Trivy: `fs` ou `repo`                                                |
| `skip_image`   | `false`                      | `full-scan`                                     | Pula a etapa de imagem do Trivy                                                                |
| `skip_lint`    | `false`                      | `full-scan`                                     | Pula a etapa do Hadolint                                                                       |
| `skip_secrets` | `false`                      | `full-scan`                                     | Pula a etapa do Betterleaks                                                                    |
| `no_git`       | `false`                      | `secret-scan`                                   | Escaneia só o working tree, sem o history do git                                               |
| `git_depth`    | `0`                          | `full-scan`, `repo-scan`, `secret-scan`         | Profundidade do clone. Mantenha `0` para o Betterleaks percorrer o history inteiro             |
| `sbom`         | `false`                      | `full-scan`, `image-scan`, `filesystem-scan`    | Gera também um SBOM                                                                            |
| `sbom_format`  | `cyclonedx`                  | os mesmos de `sbom`                             | `cyclonedx` ou `spdx-json`                                                                     |

### Trivy

Em `full-scan`, `image-scan`, `filesystem-scan`, `config-scan` e `repo-scan`.

| Input                       | Default da imagem                  | Notas                                                                                                    |
| --------------------------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `trivy_severity`            | `UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL` | Severidades gravadas no relatório                                                                        |
| `trivy_severity_fail`       | `HIGH,CRITICAL`                    | Severidades que disparam o gate                                                                          |
| `trivy_ignore_unfixed`      | `false`                            | Tira do relatório as vulnerabilidades sem fix. Não existe no `config-scan`                               |
| `trivy_ignore_unfixed_fail` | `true`                             | O gate só considera vulnerabilidades que têm fix. Não existe no `config-scan`                            |
| `trivy_exit_code`           | `1`                                | `0` desliga o gate do Trivy                                                                              |
| `trivy_format`              | `json`                             | `json`, `sarif` ou `table`; também `cyclonedx` ou `spdx-json`, exceto no `config-scan`                   |
| `trivy_scanners`            | o do próprio Trivy                 | Ex.: `vuln,secret,misconfig,license`. Não existe no `config-scan`                                        |
| `trivy_timeout`             | `10m`                              | Ex.: `15m`                                                                                               |
| `trivy_server`              | —                                  | Endpoint de um Trivy server; defina o `TRIVY_TOKEN` como variável mascarada. Não existe no `config-scan` |
| `trivy_ignorefile`          | detectado automaticamente          | Path de um arquivo `.trivyignore`                                                                        |

### Hadolint

Em `dockerfile-lint` e `full-scan`.

| Input                       | Default da imagem | Notas                                                              |
| --------------------------- | ----------------- | ------------------------------------------------------------------ |
| `hadolint_failure_level`    | `error`           | Menor nível que falha: `error`, `warning`, `info`, `style`, `none` |
| `hadolint_config`           | —                 | Path de um arquivo `.hadolint.yaml`                                |
| `hadolint_format`           | `json`            | `json`, `tty` ou `sarif`                                           |
| `hadolint_log_max_findings` | `20`              | Findings detalhados no log. Só no `dockerfile-lint`                |

### Betterleaks

Em `secret-scan` e `full-scan`.

| Input                          | Default da imagem | Notas                                                              |
| ------------------------------ | ----------------- | ------------------------------------------------------------------ |
| `betterleaks_fail_on_findings` | `true`            | Falha quando um secret é detectado                                 |
| `betterleaks_redact`           | `100`             | Percentual de cada secret mascarado no relatório (`0`–`100`)       |
| `betterleaks_baseline`         | —                 | Path de um `betterleaks-baseline.json` com os findings aceitos     |
| `betterleaks_config`           | —                 | Path de um arquivo `.betterleaks.toml`                             |
| `betterleaks_format`           | `json`            | `json`, `csv`, `junit`, `sarif` ou `template`. Só no `secret-scan` |
| `betterleaks_log_max_findings` | `20`              | Findings detalhados no log. Só no `secret-scan`                    |

### Webhook do relatório

Em todos os templates.

| Input                  | Default da imagem | Notas                                                       |
| ---------------------- | ----------------- | ----------------------------------------------------------- |
| `report_url`           | —                 | URLs separadas por vírgula que recebem o relatório por POST |
| `report_fail_on_error` | `false`           | Falha o job quando o envio falha                            |

O bearer token é um secret: defina o `REPORT_TOKEN` como variável de CI/CD
mascarada, veja [Secrets](#-secrets).

Os inputs das ferramentas correspondem um a um às variáveis de ambiente
documentadas no
[README da imagem](https://github.com/Tooark/base-images/blob/main/security-scanner/README.pt-BR.md):
`trivy_severity` define `TRIVY_SEVERITY`, `betterleaks_redact` define
`BETTERLEAKS_REDACT`, e assim por diante. Uma variável sem input próprio — ou
um input que determinado template não declara — é definida como variável de
CI/CD; veja [Como funciona a precedência](#-como-funciona-a-precedência).

---

## 📊 Relatórios

Tudo vai para o `reports_dir` e fica guardado como artifact do job, inclusive
quando o job falha.

| Template          | Relatório da ferramenta                                                        | Envelope `ark-report-tools`       |
| ----------------- | ------------------------------------------------------------------------------ | --------------------------------- |
| `full-scan`       | os arquivos abaixo, por etapa; o relatório do lint é `hadolint-<arquivo>.json` | `full-scan-report.json`           |
| `image-scan`      | `trivy-image.json`                                                             | `ark-report-image-scan.json`      |
| `filesystem-scan` | `trivy-filesystem.json`                                                        | `ark-report-filesystem-scan.json` |
| `config-scan`     | `trivy-config.json`                                                            | `ark-report-config-scan.json`     |
| `repo-scan`       | `trivy-repo.json`                                                              | `ark-report-repo-scan.json`       |
| `dockerfile-lint` | `hadolint.json`                                                                | `ark-report-dockerfile-lint.json` |
| `secret-scan`     | `betterleaks.json`                                                             | `ark-report-secret-scan.json`     |

O envelope é o formato estável: a saída da ferramenta embrulhada com o alvo do
scan, o projeto, o commit e a imagem do scanner que a produziu. É o que o
`report_url` recebe. O `sbom: true` acrescenta `trivy-image.sbom.json` ou
`trivy-filesystem.sbom.json`, e um `trivy_format` diferente de `json`
acrescenta uma cópia convertida ao lado do relatório JSON, como
`trivy-filesystem.sarif`.

---

## 🔀 Como funciona a precedência

Todo ajuste resolve na mesma ordem:

```text
input  >  variável de CI/CD  >  default da imagem
```

Um **input vazio nunca é repassado**. Isso é proposital: permite que um
projeto, ou um grupo inteiro, defina `TRIVY_SEVERITY` uma vez como variável de
CI/CD e deixe o input em branco em todos os includes, em vez de repetir o
valor. Definir os dois faz o input vencer.

```yaml
variables:
  TRIVY_SEVERITY: "CRITICAL,HIGH" # todos os scans deste pipeline
  HADOLINT_FAILURE_LEVEL: "warning"

include:
  - remote: "https://raw.githubusercontent.com/Tooark/template-security-scanner/v1.3.0/templates/filesystem-scan.yml"
  - remote: "https://raw.githubusercontent.com/Tooark/template-security-scanner/v1.3.0/templates/dockerfile-lint.yml"
```

O job roda dentro da imagem do scanner, então toda variável de CI/CD chega
direto nas ferramentas — inclusive as que não têm input, como
`TRIVY_SKIP_DB_UPDATE` ou `REPORT_METHOD`.

Duas exceções, ambas sobre paths. O `scan_path` sempre carrega um valor, então
ele vence uma variável `FULL_SCAN_PATH`. E `REPORT_DIR` e `TRIVY_CACHE_DIR` não
são para você definir como variável de CI/CD: o job declara os artifacts e o
cache em cima dos paths que o template escolheu, via `reports_dir`.

---

## 🔑 Secrets

Valores de input aparecem na configuração renderizada do pipeline, então
secrets nunca vão como input. Defina como variável de CI/CD **mascarada** em
_Settings > CI/CD > Variables_, no projeto ou no grupo, e o job as recebe:

`TRIVY_TOKEN`, `TRIVY_USERNAME`, `TRIVY_PASSWORD`, `REPORT_TOKEN`,
`REPORT_HEADERS`, `REPORT_SBOM_URL`, `REPORT_SBOM_TOKEN`.

Uma variável **protegida** só chega a jobs de branches e tags protegidas; um
scan num merge request de uma feature branch não vai enxergá-la.

O Betterleaks reda todos os secrets do relatório por padrão
(`betterleaks_redact: "100"`), e o log do job imprime só regra, arquivo, linha
e commit curto — nunca o conteúdo do secret.

---

## 🍳 Receitas

**Escanear a imagem que o pipeline enviou para o registry do projeto.** O
registry é privado a menos que o projeto seja público, então entregue ao Trivy
as credenciais do próprio job, redeclarando o job gerado:

```yaml
include:
  - remote: "https://raw.githubusercontent.com/Tooark/template-security-scanner/v1.3.0/templates/image-scan.yml"
    inputs:
      image: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"

"security:image-scan":
  needs: ["build"]
  variables:
    TRIVY_USERNAME: "$CI_REGISTRY_USER"
    TRIVY_PASSWORD: "$CI_REGISTRY_PASSWORD"
```

**Rodar o mesmo template duas vezes.** Dê ao segundo include o seu próprio
`job_name`, e o seu próprio `reports_dir` para que os artifacts dos dois não se
sobrescrevam num job posterior que baixe ambos:

```yaml
include:
  - remote: "https://raw.githubusercontent.com/Tooark/template-security-scanner/v1.3.0/templates/dockerfile-lint.yml"
  - remote: "https://raw.githubusercontent.com/Tooark/template-security-scanner/v1.3.0/templates/dockerfile-lint.yml"
    inputs:
      job_name: "security:dockerfile-lint-worker"
      dockerfile: "$CI_PROJECT_DIR/docker/Dockerfile.worker"
      reports_dir: "scan-reports/worker"
```

**Escanear só em merge requests.** Substitua o `rules`:

```yaml
include:
  - remote: "https://raw.githubusercontent.com/Tooark/template-security-scanner/v1.3.0/templates/secret-scan.yml"
    inputs:
      rules:
        - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

**Aceitar um finding conhecido.** Commite um `.trivyignore` na raiz do projeto
— ele é detectado automaticamente — ou um baseline do Betterleaks:

```yaml
include:
  - remote: "https://raw.githubusercontent.com/Tooark/template-security-scanner/v1.3.0/templates/secret-scan.yml"
    inputs:
      betterleaks_baseline: ".security/betterleaks-baseline.json"
```

**Reportar sem bloquear.** O `allow_failure: true` transforma um gate disparado
em um aviso no pipeline:

```yaml
include:
  - remote: "https://raw.githubusercontent.com/Tooark/template-security-scanner/v1.3.0/templates/filesystem-scan.yml"
    inputs:
      allow_failure: true
```

---

## 🔩 Sobrescrevendo o que os inputs não expõem

Um job gerado é um job comum. Redeclare-o pelo nome para mudar o que os inputs
não cobrem:

```yaml
"security:full-scan":
  needs: ["build"]
  services:
    - docker:27-dind
  cache: [] # desliga o cache do banco do Trivy
  variables:
    TRIVY_SCANNERS: "vuln,secret,misconfig,license"
```

O GitLab mescla as duas definições chave a chave, então o override só precisa
citar o que muda. Se você renomeou o job com `job_name`, redeclare esse nome.

---

## 💾 Cache do banco do Trivy

Baixar o banco de vulnerabilidades a cada build é a parte mais lenta do scan e
o jeito mais fácil de esbarrar em rate limit de registry, então os templates
cacheiam. O `dockerfile-lint` e o `secret-scan` não usam cache — o Hadolint e o
Betterleaks nunca leem o banco.

O `TRIVY_CACHE_DIR` aponta para `$CI_PROJECT_DIR/.cache/trivy`, e esse path é
cacheado sob a chave fixa `ark-trivy-db`, então todas as branches compartilham
um banco só. O cache é salvo com `when: always`: um gate disparado falha o job
por design, e o GitLab não salva o cache de um job que falhou a menos que isso
seja pedido.

> Em instância self-hosted, o cache do runner fica no disco do próprio runner
> por padrão. Com vários runners, o job só acerta o cache quando cai no runner
> que o escreveu. Configurar
> [distributed caching](https://docs.gitlab.com/runner/configuration/autoscale/#distributed-runners-caching)
> (S3 ou equivalente) no `config.toml` é o que torna a taxa de acerto
> consistente.

| Objetivo             | Como                                                  |
| -------------------- | ----------------------------------------------------- |
| Desligar o cache     | Redeclare o job com `cache: []`                       |
| Reusar sem atualizar | `TRIVY_SKIP_DB_UPDATE: "true"` como variável de CI/CD |

Um banco cacheado ainda é atualizado quando o Trivy o considera desatualizado;
o cache economiza o download, não congela os dados. O `TRIVY_SKIP_DB_UPDATE`
congela de fato, trocando precisão do resultado por velocidade — a imagem
repassa a variável para o Trivy, que a lê nativamente.

---

## 🐳 Qual imagem gerou o relatório

O envelope `ark-report-tools` traz um objeto `image` com o scanner que gerou o
relatório. A imagem só conhece a própria versão de build, então os templates
passam o resto: `ARK_IMAGE_NAME` e `ARK_IMAGE_TAG` vêm de `scanner_image` e
`scanner_version`, e assim um mirror ou uma tag flutuante fica registrado como
rodou. O GitLab não expõe o digest da imagem do job; defina `ARK_IMAGE_DIGEST`
como variável de CI/CD para registrá-lo, o que torna o `image.reference` um
`nome@sha256:…` imutável. Uma variável de CI/CD sobrescreve as três.

---

## 🔐 Notas de segurança

Três pontos valem saber antes de plugar isso num pipeline que tem credenciais.

**Relatórios podem conter os secrets que encontraram.** Duas configurações
transformam um artifact em vazamento: `betterleaks_redact: "0"` grava os
secrets detectados em claro, e incluir `secret` em `trivy_scanners` coloca os
achados do Trivy no relatório. Artifacts são baixáveis por qualquer um com
acesso de leitura ao projeto, então mantenha a redação no default a menos que
o destino do artifact seja tão restrito quanto os secrets.

**Tags flutuantes são mutáveis por design.** Cada release move `v1` e `v1.0` à
força, então pinar qualquer uma das duas significa rodar no seu pipeline código
que você não revisou, depois do próximo release. A `v1.0.0` nunca é movida, mas
uma tag do GitHub pode em princípio ser reescrita por quem tem push; um remote
include pinado num commit SHA é a única referência totalmente imutável:

```yaml
include:
  - remote: "https://raw.githubusercontent.com/Tooark/template-security-scanner/<commit-sha>/templates/full-scan.yml"
```

**Um remote include é baixado quando o pipeline é criado.** Se o
`raw.githubusercontent.com` estiver inacessível nesse momento, o pipeline nem
chega a ser criado. Uma instância que não pode depender disso deve publicar os
templates no seu próprio CI/CD Catalog pelo projeto-espelho.

### O que foi verificado

Há `eval` nos templates, mas ele só itera uma lista fixa de nomes de variável —
nenhum input chega nele. Os inputs chegam ao script do job como variáveis de
ambiente, nunca colados nele como texto, e o `scripts/validate-templates.py`
quebra o CI de um template que faça isso. O word splitting do `extra_args` é
proposital e roda sob `set -f`, então um valor como `*` não expande contra os
arquivos do repositório. O `tests/templates.test.py` verifica tudo isso a cada
commit, e os blocos de script dos templates passam pelo ShellCheck. Os scripts
de validação usam `yaml.safe_load`. Os tokens dos workflows são escopados:
`contents: read` no CI, `contents: write` só no job de release. A imagem de
terceiro do `actionlint` está pinada por digest, e o Dependabot acompanha o
resto.

---

## 🔖 Versionamento

Os releases são taggeados como `vMAJOR.MINOR.PATCH`. Cada release também move
duas tags flutuantes, para acompanhar uma linha sem editar pipeline a cada
patch:

| Referência | Resolve para                   | Use quando                            |
| ---------- | ------------------------------ | ------------------------------------- |
| `v1.0.0`   | Exatamente aquele release      | Pipeline reproduzível                 |
| `v1.0`     | Patch mais novo da 1.0         | Atualização automática de patch       |
| `v1`       | Release mais novo da linha 1.x | Atualização automática de minor/patch |
| `main`     | Trabalho não publicado         | Nunca em pipeline que importa         |

Um componente de catálogo usa a versão sem prefixo — `@1.0.0`, `@1.0`, `@1` —
porque é assim que o catálogo nomeia os releases.

O [`VERSION`](VERSION) é a fonte única de verdade tanto da versão do componente
quanto da tag da imagem que todos os templates pinam. O
`scripts/check-sync.sh` quebra o CI se algum deles divergir, e o workflow de
release recusa uma tag que não bata com `COMPONENT_VERSION`.

Subir a versão da imagem é, portanto, uma mudança de três linhas: edite o
`VERSION`, rode `./scripts/check-sync.sh` e atualize os pins que ele apontar.

---

## 📦 Publicação

### GitHub Releases

Envie uma tag `v*.*.*`. O [`.github/workflows/release.yml`](https://github.com/Tooark/template-security-scanner/blob/main/.github/workflows/release.yml)
roda as checagens, compara a tag com o `VERSION`, cria o release com notas
geradas e move as tags flutuantes. Um remote include pode usar a tag assim que
ela existir.

### GitLab CI/CD Catalog

O catálogo só lista componentes hospedados na própria instância do GitLab,
então um repositório do GitHub não pode ser publicado nele diretamente.
Configure o projeto-espelho descrito em
[`catalog-mirror/`](https://github.com/Tooark/template-security-scanner/tree/main/catalog-mirror):
ele consulta os releases daqui num agendamento, copia o `templates/` quando a
versão muda e publica no catálogo da sua instância.

---

## 🚧 Armadilhas

**O override de entrypoint é obrigatório.** O entrypoint da imagem executa o
`ark-tools` diretamente, e o GitLab Runner mantém o entrypoint da imagem e
anexa um shell a ele. Todos os templates definem `entrypoint: [""]`; removê-lo
num override quebra o job antes do script rodar.

**`GIT_DEPTH: "0"` importa para o scan de secrets.** O Betterleaks percorre o
history do git. Com o clone raso padrão do GitLab, ele silenciosamente quase
não vê nada. Os templates definem `git_depth: "0"`; diminua só quando o history
for grande demais para clonar e você aceitar escanear menos.

**O stage precisa existir.** O default é `test`, que todo pipeline tem, a menos
que declare `stages:` sem ele. Um pipeline com a própria lista de stages
precisa incluir `test` ou passar o `stage`.

**Booleanos e strings não são intercambiáveis.** `sbom: "true"` e
`no_git: true` são ambos rejeitados: o primeiro é um input booleano recebendo
uma string, o segundo um input string recebendo um booleano. Veja
[Inputs](#-inputs).

**Imagem privada precisa de credenciais.** O `image-scan` e a etapa de imagem
do `full-scan` baixam a imagem do registry por conta própria. Para o registry
do próprio projeto, passe as credenciais do job como mostrado em
[Receitas](#-receitas).

**O dockerfile-lint trata um arquivo por job.** Use `full-scan` com
`dockerfiles: "a,b,c"`, ou inclua o `dockerfile-lint` uma vez por arquivo com
`job_name` diferente.

**O default vazio de `tags` renderiza como `tags: []`.** O GitLab não tem como
um input omitir uma keyword, e uma lista vazia de tags é como se diz "qualquer
runner". Os pipelines aceitam; só o JSON schema do editor do GitLab rejeita
arrays vazios
([gitlab#551088](https://gitlab.com/gitlab-org/gitlab/-/issues/551088)), e esse
schema vale para arquivos `.gitlab-ci.yml`, não para estes templates.

---

## 📁 Estrutura do repositório

```text
templates/                  Os templates de componente, um job cada
examples/                   Pipelines prontos para copiar
catalog-mirror/             Projeto-espelho que publica em um CI/CD Catalog
scripts/                    Checagens rodadas no CI e localmente
tests/                      Testes dos jobs gerados, sem precisar de GitLab
docs/                       Guia de onboarding, publicado no GitHub Pages
SUPPORTED-INTEGRATIONS.md   Versões do GitLab, runners e executors suportados
VERSION                     Fonte única de verdade das versões
```

---

## 🧪 Desenvolvimento

```bash
python3 -m pip install pyyaml

python3 scripts/validate-templates.py   # estrutura, wiring de inputs, inputs mortos
./scripts/check-sync.sh                 # pins de versão, wiring de ARK_IN_*, docs
python3 scripts/check-examples.py       # exemplos e trechos do README batem com os templates
python3 tests/templates.test.py         # o job que cada template gera, sem GitLab
shellcheck -s bash scripts/*.sh
```

O CI roda os cinco, passa os blocos de script dos templates pelo ShellCheck,
roda o `actionlint` e escaneia este repositório com a GitHub Action irmã.

Ao adicionar um input, mexa nos quatro lugares ou as checagens vão avisar: o
`spec:inputs` do template, o bloco `variables:` como `ARK_IN_*`, o script do job
que o lê e as tabelas dos dois READMEs. O
[`CONTRIBUTING.md`](https://github.com/Tooark/template-security-scanner/blob/main/CONTRIBUTING.md)
tem os detalhes.

---

## 🔗 Projetos relacionados

| Projeto                                                                                  | O que é                                                         |
| ---------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| [`Tooark/action-security-scanner`](https://github.com/Tooark/action-security-scanner)    | Os mesmos scans como uma GitHub Action                          |
| [`Tooark/base-images`](https://github.com/Tooark/base-images/tree/main/security-scanner) | A imagem `security-scanner`: as ferramentas e o CLI `ark-tools` |

---

## 🤝 Contribuição

Contribuições são bem-vindas! Comece pelo
[CONTRIBUTING.md](https://github.com/Tooark/template-security-scanner/blob/main/CONTRIBUTING.md)
— ele descreve o que pertence a este repositório e o que pertence à imagem do
scanner, o fluxo de desenvolvimento, como adicionar um input, a convenção de
commits e o processo de release.

Em resumo:

- Rode as cinco checagens de [Desenvolvimento](#-desenvolvimento) antes de abrir um PR
- Um input novo entra em quatro lugares, ou as checagens quebram o build
- Mantenha o `README.md` e o `README.pt-BR.md` em sincronia
- Os commits seguem o [Conventional Commits](https://www.conventionalcommits.org/)
- Registre no `CHANGELOG.md`, em `[Unreleased]`, tudo o que quem consome vai perceber

Ao participar, você concorda com o [Código de Conduta](https://github.com/Tooark/template-security-scanner/blob/main/CODE_OF_CONDUCT.md).

---

## 🆘 Ajuda e Segurança

- ❓ **Dúvidas, bugs e ideias** — veja o [SUPPORT.md](https://github.com/Tooark/template-security-scanner/blob/main/SUPPORT.md) para escolher o canal certo
- 🔒 **Vulnerabilidades de segurança** — **não** abra issue pública; siga o [SECURITY.md](https://github.com/Tooark/template-security-scanner/blob/main/SECURITY.md)
- 🐳 **Problema dentro do próprio scanner** — Trivy, Hadolint, Betterleaks e o `ark-tools` ficam em [`Tooark/base-images`](https://github.com/Tooark/base-images/tree/main/security-scanner)

---

## 💖 Apoie

Se estes templates ajudam nos seus pipelines, considere apoiar o desenvolvimento:

- 💙 [GitHub Sponsors](https://github.com/sponsors/paulosfjunior)
- ☕ [Ko-fi](https://ko-fi.com/paulosfjunior)

Cada contribuição ajuda a manter o projeto ativo e em evolução. Obrigado! 🙏

---

## 📝 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).
