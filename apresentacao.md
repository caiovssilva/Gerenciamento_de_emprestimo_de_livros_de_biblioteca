# Apresentação técnica da aplicação da biblioteca

## 1. Identificação do documento

**Projeto:** Gerenciamento de empréstimos da Biblioteca Narceu de Paiva Filho  
**Documento analisado:** `Documentacao_Biblioteca_Corrigida_Caio_Vitor_Soares_Silva.pdf.pdf`  
**Relatório:** apresentação técnica, funcional e de qualidade  
**Data de referência:** 30/10/2026, conforme a documentação analisada  
**Responsável indicado no documento:** Caio Vitor Soares Silva  
**Instituição:** EEEFM Narceu de Paiva Filho

Este relatório transforma a documentação da aplicação em uma visão consolidada do projeto. O objetivo é apresentar o que o sistema pretende fazer, como foi estruturado, quais evidências foram obtidas, quais limitações permanecem e quais ações devem ser priorizadas antes de uma utilização real.

> **Nota de escopo:** este relatório analisa o conteúdo do PDF e os achados de auditoria já registrados no repositório. Ele não substitui uma validação de produção, um teste de intrusão ou uma inspeção direta do banco remoto.

## 2. Resumo executivo

A aplicação é um sistema web para organizar o acervo, os alunos, os exemplares e a circulação de livros. Ela combina uma interface em HTML, CSS e JavaScript com uma API Flask em Python e um banco Supabase/PostgreSQL. Os principais fluxos incluem cadastro de livros, identificação de exemplares por QR Code, cadastro e consulta de alunos, empréstimos, devoluções, renovações, relatórios e exportação de dados.

A documentação está bem estruturada e possui uma qualidade importante: separa funcionalidades mostradas em capturas de tela de comportamentos efetivamente testados. Ela também reconhece que o banco remoto, a câmera física, o navegador publicado, o RLS e a concorrência não foram validados diretamente.

Entretanto, o sistema ainda não pode ser considerado pronto para produção. A principal preocupação é de segurança: há evidências de credenciais padrão, exposição potencial da chave privilegiada do Supabase, rotas sem autorização centralizada, políticas RLS permissivas e mecanismos frágeis de sessão e definição de papéis. Também existem problemas de integridade de empréstimos, XSS, CSRF, dependências e cobertura de testes.

### Classificação geral

| Área | Avaliação | Situação |
|---|---|---|
| Documentação | Boa | Organizada, contextualizada e transparente quanto às limitações |
| Funcionalidades | Parcialmente demonstradas | As telas estão documentadas, mas várias operações não foram comprovadas de ponta a ponta |
| Testes | Insuficientes para produção | 180 de 192 testes Python aprovados; 12 falharam |
| Frontend | Funcional, com riscos | 7 de 7 testes JavaScript aprovados, mas há risco de XSS e exposição de identidade |
| Backend | Requer endurecimento | Regras de negócio existem, porém a autorização não está aplicada de forma uniforme |
| Banco de dados | Requer revisão | Há riscos de RLS, cascatas destrutivas, integridade e ausência de migrations |
| Segurança | Crítica | O acesso administrativo e a proteção de dados podem ser comprometidos |

## 3. O que a documentação apresenta

O PDF possui 59 páginas e está dividido em cinco blocos principais:

1. **Contexto e objetivo:** explica o problema do controle manual e a finalidade da aplicação.
2. **Código da aplicação:** apresenta tecnologias, caminhos reais de arquivos e trechos de backend e frontend.
3. **Modelagem da aplicação:** mostra casos de uso, fluxos operacionais e entidades do banco.
4. **Testes da aplicação:** informa os testes preparados, resultados obtidos e o que ainda não foi verificado.
5. **Treinamento do usuário:** descreve as telas e os procedimentos para uso do sistema.

A documentação informa que as capturas da interface foram feitas em 18/10/2026, enquanto o código e os testes foram auditados em 30/10/2026. Essa diferença deve ser considerada ao interpretar as imagens: uma captura demonstra a aparência da interface naquele momento, mas não garante que o comportamento atual permaneça igual.

## 4. Objetivo e contexto do sistema

Segundo o documento, antes da aplicação o controle de livros, alunos e datas era feito com papel, pastas ou registros pouco centralizados. Esse modelo dificultava a consulta, o acompanhamento dos prazos e a identificação de exemplares.

O sistema foi criado para:

- centralizar informações da biblioteca;
- facilitar a busca de livros e alunos;
- organizar exemplares individuais;
- acompanhar empréstimos, prazos, devoluções e atrasos;
- reduzir confusões e perdas de livros;
- disponibilizar relatórios para acompanhamento da circulação.

Esses objetivos são coerentes com os módulos documentados. Contudo, a efetividade do sistema depende de as regras de autorização, integridade e auditoria serem aplicadas no servidor e no banco, e não somente na interface.

## 5. Arquitetura técnica

### 5.1 Fluxo principal

O fluxo descrito no PDF é:

```text
Usuário
  -> Frontend HTML/CSS/JavaScript
  -> API Flask
  -> Regras de validação e negócio
  -> Supabase/PostgreSQL
  -> Resposta para atualização da interface
```

O frontend apresenta telas, formulários, tabelas, modais, gráficos, leitura de códigos e chamadas HTTP. O backend recebe as solicitações, valida dados, consulta registros e grava alterações. O Supabase/PostgreSQL armazena as entidades e os relacionamentos.

### 5.2 Tecnologias citadas

- **Frontend:** HTML, CSS e JavaScript.
- **Leitura de códigos:** `jsQR`, `BarcodeDetector`, `qrcode`, OpenCV, Pillow e PyZbar.
- **Backend:** Python e Flask.
- **Gráficos:** Chart.js.
- **Banco:** Supabase/PostgreSQL.
- **Integrações:** fontes externas para consulta de ISBN e serviços de inteligência artificial/visão, conforme configuração do projeto.
- **Hospedagem documentada:** Render.

### 5.3 Organização do código

Os caminhos destacados na documentação incluem:

- [backend/app.py](backend/app.py): inicialização do Flask, configuração e registro das rotas.
- [backend/api/auth.py](backend/api/auth.py): login, sessão e configuração relacionada à autenticação.
- [backend/api/books.py](backend/api/books.py): livros, exemplares, ISBN e consultas externas.
- [backend/api/students.py](backend/api/students.py): alunos, carteirinhas e perfis.
- [backend/api/loans.py](backend/api/loans.py): empréstimos, devoluções e renovações.
- [backend/api/reports.py](backend/api/reports.py): relatórios e exportações.
- [backend/scanner/routes.py](backend/scanner/routes.py): leitura, geração e processamento de QR Code.
- [frontend/assets/js/api.js](frontend/assets/js/api.js): comunicação do frontend com a API.
- [database.sql](database.sql): estrutura, tabelas, relacionamentos, políticas e views do banco.

## 6. Funcionalidades documentadas

### 6.1 Acervo e livros

O módulo de livros permite consultar e manter o catálogo. A tela apresenta título, autor, ISBN ou identificador, gênero, área, quantidade de exemplares e disponibilidade.

O cadastro pode receber dados bibliográficos manualmente ou consultar informações por ISBN. O código normaliza o ISBN removendo caracteres não numéricos e validando o formato. A documentação informa que podem ser consultadas fontes como Google Books, ISBNsearch e Open Library.

**Ponto de atenção:** consultas externas podem ser lentas, falhar, retornar dados divergentes ou consumir limites de API. O resultado deve ser revisado antes de salvar.

### 6.2 Exemplares e QR Codes

O sistema diferencia o livro do exemplar físico. Um livro pode ter várias cópias, e cada cópia possui um identificador utilizado em operações de empréstimo e devolução.

O QR Code do exemplar deve identificar a mesma cópia que foi emprestada. A documentação orienta a conferência do livro, aluno, prazo e exemplar antes da confirmação.

**Ponto de atenção:** a captura de tela do scanner não comprova que uma leitura física foi concluída. A câmera, permissões do navegador e compatibilidade do dispositivo ainda precisam de testes reais.

### 6.3 Alunos e carteirinhas

O módulo de alunos permite consultar por nome, turma ou carteirinha, importar dados por CSV, cadastrar sala e gerar carteirinhas. Também existe um fluxo relacionado à concessão de acesso de bibliotecário.

**Ponto de atenção:** a concessão de privilégios não pode depender apenas de uma ação visual da tela ou de um campo recebido do cliente. Deve exigir autorização administrativa validada no servidor.

### 6.4 Empréstimos, devoluções e renovações

O fluxo documentado é:

1. localizar o aluno;
2. localizar o livro;
3. selecionar e conferir o exemplar;
4. definir o prazo;
5. confirmar o empréstimo;
6. devolver usando o QR Code da cópia correta;
7. consultar histórico e situação do aluno.

O backend possui validações para campos obrigatórios e para a correspondência do QR Code na devolução. Apesar disso, a auditoria identificou que disponibilidade e gravação não são atômicas. Duas solicitações concorrentes podem tentar reservar o mesmo exemplar antes que uma delas seja registrada.

Também não foi identificado limite máximo de renovações, cálculo de multa ou bloqueio por atraso. O campo `renovacoes` é incrementado, mas não existe uma regra suficiente para impedir renovações indefinidas.

### 6.5 Painel e relatórios

O painel apresenta indicadores de exemplares, empréstimos, alunos e atrasos. Os relatórios permitem acompanhar a circulação e exportar dados em CSV.

Essas funções são sensíveis porque exibem dados pessoais e operacionais. A autorização deve ser conferida em cada requisição, inclusive quando a chamada é feita diretamente por um cliente que não utiliza a interface.

### 6.6 Autoatendimento

O autoatendimento orienta o aluno a ler a própria carteirinha e seguir o fluxo liberado pelo sistema. A documentação informa que esse modo depende de configuração e habilitação pelo responsável.

**Ponto de atenção:** QR Code de aluno não deve conceder privilégios administrativos sem uma segunda prova de identidade. O navegador e o conteúdo do QR Code são controláveis pelo usuário.

## 7. Modelo de dados

As entidades descritas no PDF incluem salas, gêneros, livros, alunos, empréstimos, usuários e relatórios mensais.

| Entidade | Função principal |
|---|---|
| `salas` | Organiza salas e capacidade |
| `generos` | Classifica livros |
| `livros` | Armazena dados bibliográficos e exemplares |
| `alunos` | Guarda estudantes, turma, sala e identificação |
| `emprestimos` | Relaciona aluno, livro, exemplar, datas e devolução |
| `usuarios` | Armazena credenciais e dados de acesso |
| `relatorios_mensais` | Guarda informações agregadas ou geradas |

O modelo guarda os exemplares em uma estrutura JSONB dentro de livros e referencia a cópia no empréstimo. Essa escolha pode funcionar, mas exige validação estrutural e regras de integridade adicionais para impedir identificadores duplicados, exemplares inexistentes ou divergência entre quantidade e lista de cópias.

## 8. Testes e evidências

### 8.1 Resultados registrados

O PDF informa os seguintes números:

| Suíte | Resultado |
|---|---:|
| Testes Python | 180 aprovados de 192; 12 reprovados; 1 aviso |
| Testes JavaScript | 7 aprovados de 7; nenhum reprovado |

As execuções foram repetidas em 30/10/2026 e os resultados permaneceram iguais. A repetição confirma a reprodutibilidade daquele estado de testes, mas não transforma os 12 testes reprovados em comportamento aceitável.

### 8.2 O que foi exercitado

Foram documentados cenários relacionados a:

- campos obrigatórios no empréstimo;
- respostas HTTP `400`, `403`, `409` e `503`;
- devolução com QR Code incompatível;
- tentativa de renovar empréstimo devolvido;
- tentativa de devolver cópia diferente;
- autenticação por carteirinha;
- consulta de ISBN;
- geração de carteirinhas e cartões de exemplares;
- relatórios e exportação;
- navegação e componentes do frontend.

### 8.3 O que não foi comprovado

O documento declara que ainda não foram validados diretamente:

- banco Supabase remoto;
- RLS funcionando com papéis reais;
- escrita real no banco em todos os fluxos;
- concorrência em empréstimos e devoluções;
- carga e limites das integrações externas;
- câmera física em dispositivo real;
- execução completa dos fluxos no navegador publicado;
- cobertura de linhas, funções e branches;
- estado atual do serviço hospedado no Render.

Assim, capturas de tela e existência de testes não devem ser apresentadas como prova de funcionamento integral.

## 9. Auditoria de segurança e qualidade

### 9.1 Riscos críticos

#### Credenciais fixas e previsíveis

O SQL contém um usuário administrativo com senha fixa em texto claro. Além disso, o backend utiliza uma chave secreta padrão quando a configuração de produção não está definida.

**Impacto:** acesso administrativo não autorizado, falsificação de sessão e comprometimento dos dados.

**Correção necessária:** remover credenciais do código e do SQL de instalação, exigir variáveis de ambiente e realizar bootstrap protegido do administrador.

#### Exposição potencial da chave privilegiada

A rota de configuração do Supabase possui fallback para `SUPABASE_SERVICE_KEY`. Essa chave não pode ser enviada ao navegador.

**Impacto:** quem obtiver a chave pode consultar ou alterar dados com privilégios elevados, contornando RLS.

**Correção necessária:** retornar somente uma chave pública apropriada, remover a rota se ela não for necessária e rotacionar qualquer segredo que tenha sido exposto.

#### Rotas sem autorização uniforme

CRUDs, relatórios, exportações e operações de QR não possuem uma camada central que exija login e papel adequado em todas as rotas.

**Impacto:** um cliente pode chamar a API diretamente e executar operações que a interface talvez apenas esconda.

**Correção necessária:** criar decoradores ou middleware de autorização no backend e testar respostas `401` e `403` para cada operação sensível.

#### RLS permissivo

O banco possui políticas com condições equivalentes a `USING (true)` e `WITH CHECK (true)`. Além disso, o uso de `service_role` contorna RLS.

**Impacto:** o banco não oferece uma barreira efetiva se a chave ou a API forem acessadas diretamente.

**Correção necessária:** revogar permissões públicas, definir políticas por papel e ownership e separar claramente o acesso público do acesso administrativo.

#### Elevação de privilégio por QR ou campo do cliente

O estado de bibliotecário pode ser influenciado por dados enviados pelo cliente ou por QR Code. Papel de usuário não pode ser aceito como verdade por estar presente no payload.

**Impacto:** usuário comum pode tentar obter acesso administrativo sem uma autorização confiável.

**Correção necessária:** manter o papel em registro protegido, validar a operação com sessão administrativa e exigir senha ou segundo fator quando houver elevação de privilégio.

### 9.2 Riscos altos

- Carteirinha administrativa contendo senha visível.
- Ausência de proteção CSRF nas mutações.
- Cookies sem exigência clara de `Secure`, `HttpOnly` e `SameSite`.
- Ausência de limite de tentativas, bloqueio ou backoff no login.
- Dados da API interpolados em `innerHTML`, com risco de XSS.
- Upload de imagem base64 sem limite e validação MIME robustos.
- Entrada de API sem schemas estritos para rejeitar campos desconhecidos.
- Operações de empréstimo suscetíveis a corrida de concorrência.
- Exclusão de alunos ou livros podendo apagar histórico por cascade.
- Ausência de limite de renovações e de regras para atraso.

### 9.3 Riscos médios e de manutenção

- Cookie do frontend guarda identidade em JSON não assinado.
- Logout não invalida a sessão no servidor de modo completo.
- Senhas legadas em texto claro ainda são aceitas.
- Logs de depuração expõem prefixos de hashes.
- CORS permite origens amplas.
- CSP ainda aceita `unsafe-inline`.
- Faltam HSTS, proteção contra framing e política de referrer.
- Dependências importantes não estão todas fixadas em versões.
- `pytest` não está declarado adequadamente nas dependências do backend.
- Não existem migrations incrementais para mudanças controladas no banco.
- Índices e constraints não cobrem todos os cenários de consulta e integridade.
- Timestamps sem timezone podem causar divergências entre ambientes.
- Campos de auditoria são texto livre e não representam uma identidade autenticada.

## 10. Priorização de correções

### Fase 1: contenção imediata

1. Revogar e rotacionar qualquer `SUPABASE_SERVICE_KEY` que possa ter sido exposta.
2. Remover a chave de serviço da resposta ao navegador.
3. Remover usuário e senha padrão do SQL e do código.
4. Exigir `SECRET_KEY` forte e exclusiva por ambiente.
5. Desabilitar operações administrativas até que exista autorização no backend.
6. Retirar senhas das carteirinhas e dos cartões impressos.

### Fase 2: autorização e sessão

1. Definir papéis persistidos e confiáveis para usuários.
2. Aplicar autenticação e autorização a todas as rotas sensíveis.
3. Implementar CSRF para operações baseadas em cookie.
4. Configurar cookies `Secure`, `HttpOnly` e `SameSite` adequados.
5. Implementar expiração, logout server-side e invalidação de sessão.
6. Adicionar limite de tentativas e backoff ao login.
7. Restringir CORS às origens necessárias.

### Fase 3: banco e regras de negócio

1. Substituir políticas RLS permissivas por políticas específicas.
2. Remover `DROP TABLE ... CASCADE` do fluxo normal de atualização.
3. Trocar cascatas destrutivas por `RESTRICT` ou soft delete quando houver histórico.
4. Criar uma operação transacional para reservar exemplar.
5. Adicionar constraint para impedir mais de um empréstimo ativo por exemplar.
6. Definir limite de renovações, regras de atraso e cálculo de multa.
7. Adicionar validação estrutural para exemplares e constraints de datas.
8. Criar migrations versionadas e reversíveis.

### Fase 4: frontend, integrações e testes

1. Substituir interpolação insegura por `textContent` ou construção explícita de elementos.
2. Validar tipo, tamanho e conteúdo dos uploads.
3. Adotar schemas de entrada e rejeitar campos inesperados.
4. Fixar versões de dependências e declarar todas as ferramentas de teste.
5. Corrigir as 12 falhas Python antes de apresentar o sistema como estável.
6. Adicionar testes de autorização, CSRF, XSS, RLS e concorrência.
7. Testar câmera em dispositivos reais e fluxos completos no navegador publicado.
8. Medir cobertura e estabelecer critérios de aprovação para release.

## 11. Plano de validação recomendado

Após as correções, a aplicação deve ser validada em camadas:

### Segurança

- tentar acessar cada rota sem sessão;
- tentar acessar rota administrativa com papel comum;
- alterar o payload para incluir `is_librarian=true`;
- confirmar que a chave de serviço nunca aparece em respostas públicas;
- verificar cookies e cabeçalhos HTTP;
- executar testes de XSS com dados de aluno, livro e gênero;
- validar CSRF em todas as mutações;
- testar limite de tentativas de login.

### Integridade de empréstimos

- enviar duas reservas simultâneas para o mesmo exemplar;
- confirmar que apenas uma é aceita;
- devolver a mesma operação duas vezes;
- renovar até o limite e tentar renovar novamente;
- tentar excluir aluno ou livro com histórico;
- validar datas inválidas e exemplares inexistentes.

### Operação real

- executar os fluxos no navegador publicado;
- testar permissões de câmera em desktop e celular;
- ler QR de aluno, QR de exemplar e ISBN reais;
- confirmar persistência no banco remoto;
- verificar relatórios depois de criar e devolver empréstimos;
- observar logs, tempo de resposta e falhas de serviços externos.

## 12. Conclusão

A documentação analisada cumpre bem o papel de apresentar a proposta, a estrutura e os fluxos da aplicação. Seu maior mérito é não confundir telas bonitas com funcionamento comprovado: ela informa quais evidências existem e quais verificações ainda faltam.

O projeto possui uma base funcional relevante, mas a situação atual exige correções antes de qualquer uso com dados reais de alunos. Os problemas prioritários estão concentrados em credenciais, autorização, exposição de chaves, RLS, sessão, integridade de empréstimos e testes incompletos.

Portanto, a conclusão técnica é:

> **A aplicação está documentada e parcialmente testada, mas ainda não está pronta para produção segura.**

O próximo marco não deve ser apenas adicionar novas telas. Deve ser uma versão de segurança e confiabilidade, com autorização centralizada, banco protegido, operações transacionais, eliminação de credenciais expostas e todos os testes críticos aprovados.

## 13. Referências do repositório

- [Documentacao_Biblioteca_Corrigida_Caio_Vitor_Soares_Silva.pdf.pdf](Documentacao_Biblioteca_Corrigida_Caio_Vitor_Soares_Silva.pdf.pdf)
- [claude.md](claude.md)
- [database.sql](database.sql)
- [backend/app.py](backend/app.py)
- [backend/api/auth.py](backend/api/auth.py)
- [backend/api/books.py](backend/api/books.py)
- [backend/api/students.py](backend/api/students.py)
- [backend/api/loans.py](backend/api/loans.py)
- [backend/api/reports.py](backend/api/reports.py)
- [backend/scanner/routes.py](backend/scanner/routes.py)
- [frontend/assets/js/app.js](frontend/assets/js/app.js)
- [frontend/assets/js/api.js](frontend/assets/js/api.js)

## 14. Limitações desta análise

- O banco remoto não foi consultado diretamente.
- Não foi feita execução de navegador ou câmera física neste relatório.
- Os resultados de testes foram aceitos conforme registrados na documentação e na auditoria existente.
- Não foi realizada nova auditoria de todas as rotas após a data registrada no PDF.
- O conteúdo do anexo textual mencionado como `Pasted text #1` não estava disponível para análise.