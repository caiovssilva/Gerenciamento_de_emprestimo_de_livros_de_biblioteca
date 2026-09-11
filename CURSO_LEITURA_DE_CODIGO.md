# Curso de Leitura de Código — Projeto de Gestão de Empréstimo de Livros

Este curso foi criado para te ajudar a aprender a ler código de forma profissional, usando o seu projeto como exemplo real.

O objetivo não é apenas entender a sintaxe, mas aprender a interpretar a lógica, a estrutura e o fluxo do sistema.

---

## Aula 1 — Entendendo o projeto como um todo

Objetivo:
Aprender a olhar um projeto e entender sua estrutura antes de entrar nos detalhes.

### O que você precisa saber
Todo projeto tem:
- entrada
- processamento
- saída

No seu caso:
- entrada: ações do usuário, login, cadastro, empréstimo
- processamento: regras do sistema
- saída: resposta na tela, dados salvos, relatórios

### Como pensar
Pergunte sempre:
- O que este projeto quer resolver?
- Quais funções ele possui?
- Quem usa esse sistema?
- Que dados ele precisa controlar?

### Conclusão da Aula 1
Você passa a enxergar o projeto como um conjunto de partes conectadas, e não como vários arquivos aleatórios.

---

## Aula 2 — Entendendo a estrutura de pastas

Objetivo:
Aprender a ler um projeto pelo formato das pastas.

### Estrutura do seu projeto
- backend: lógica do sistema
- frontend: interface visual
- data: arquivos com dados
- tests: testes do sistema

### Como ler a estrutura
- se uma pasta chama backend, provavelmente ali está a lógica
- se uma pasta chama frontend, provavelmente ali está a interface
- se existe uma pasta tests, aí estão os testes

### Conclusão da Aula 2
Você já consegue interpretar a organização do projeto antes mesmo de abrir o código.

---

## Aula 3 — Como ler um arquivo Python

Objetivo:
Ensinar a ler arquivos Python de forma correta.

### O que olhar primeiro
1. Imports
2. Funções
3. Rotas
4. Retornos

### Exemplo prático
No Python, geralmente você vê:
- bibliotecas importadas
- funções definidas
- rotas com endpoints
- respostas em JSON

### Perguntas que você deve fazer
- O que essa função faz?
- Quais dados ela recebe?
- O que ela retorna?
- Onde esses dados vêm?

### Conclusão da Aula 3
Você aprende a ler Python com foco em objetivo, não apenas em sintaxe.

---

## Aula 4 — Lendo o arquivo principal do backend

Objetivo:
Entender o ponto de entrada da aplicação.

Arquivo:
- backend/app.py

### O que esse arquivo faz
Ele é responsável por iniciar a aplicação e conectar as partes principais do sistema.

### O que olhar
- estrutura da aplicação
- rotas
- inicialização
- integração com módulos

### O que você deve aprender
- como o sistema é montado
- como o backend é iniciado
- como as rotas são registradas

### Conclusão da Aula 4
Você já entende o papel central da aplicação.

---

## Aula 5 — Lendo autenticação

Objetivo:
Entender como o sistema identifica usuários.

Arquivo:
- backend/api/auth.py

### O que esse arquivo faz
Ele cuida do login e da verificação de permissões.

### Conceitos que aparecem
- login
- senha
- validação
- acesso

### Como ler
Procure:
- a função de login
- o que a função recebe
- o que ela valida
- o que ela retorna

### Conclusão da Aula 5
Você aprende a ler lógica de segurança e autenticação.

---

## Aula 6 — Lendo o módulo de livros

Objetivo:
Entender como o sistema gerencia livros.

Arquivo:
- backend/api/books.py

### O que esse arquivo faz
Ele cuida do cadastro, busca e organização dos livros.

### O que observar
- criação de livro
- busca por identificador
- relacionamento com QR code
- controle de exemplares

### Conclusão da Aula 6
Você aprende a entender módulos que representam entidades do sistema.

---

## Aula 7 — Lendo o módulo de alunos

Objetivo:
Entender o cadastro e a identificação de alunos.

Arquivo:
- backend/api/students.py

### O que esse arquivo faz
Ele controla os alunos, turma, carteirinha e QR.

### O que observar
- cadastro do aluno
- busca pelo aluno
- identificação por QR
- diferenciação entre usuários comuns e bibliotecários

### Conclusão da Aula 7
Você aprende a acompanhar dados de um objeto do sistema.

---

## Aula 8 — Lendo o módulo de empréstimos

Objetivo:
Entender a lógica central do projeto.

Arquivo:
- backend/api/loans.py

### O que esse arquivo faz
Ele gerencia:
- empréstimo
- devolução
- renovação
- controle de disponibilidade

### O que observar
- quando um empréstimo é criado
- como o sistema valida se o livro pode sair
- como a devolução é registrada

### Conclusão da Aula 8
Você entende o fluxo principal da aplicação.

---

## Aula 9 — Lendo o frontend

Objetivo:
Entender como a interface conversa com o backend.

Arquivo:
- frontend/assets/js/app.js

### O que esse arquivo faz
Ele controla a navegação e as ações do usuário.

### O que observar
- eventos
- funções
- chamadas para API
- mudanças na tela

### Conclusão da Aula 9
Você aprende a ligar a lógica do backend com a experiência do usuário.

---

## Aula 10 — Lendo as páginas do frontend

Objetivo:
Entender as telas principais do sistema.

Arquivos:
- frontend/assets/js/pages/books.js
- frontend/assets/js/pages/students.js
- frontend/assets/js/pages/loans.js

### O que observar
- como cada página é montada
- como os botões funcionam
- como os dados aparecem na interface

### Conclusão da Aula 10
Você começa a compreender a comunicação entre tela e lógica.

---

## Aula 11 — Lendo o CSS

Objetivo:
Entender como a interface é estilizada.

Arquivo:
- frontend/assets/css/main.css

### O que observar
- layout
- cores
- responsividade
- organização visual

### Conclusão da Aula 11
Você aprende que código não é só lógica; também é experiência visual.

---

## Aula 12 — Entendendo testes

Objetivo:
Aprender a verificar se o sistema funciona corretamente.

Pasta:
- backend/tests

### O que observar
- o que cada teste valida
- qual comportamento é esperado
- como o projeto é defendido contra erros

### Conclusão da Aula 12
Você começa a pensar como um programador profissional, testando antes de afirmar que algo funciona.

---

## Aula 13 — Como ler código como profissional

Objetivo:
Adquirir a mentalidade correta de leitura de código.

### Regras profissionais
- leia o objetivo do arquivo
- identifique funções principais
- siga o fluxo de dados
- relacione arquivos
- faça perguntas sobre comportamento
- não tente entender tudo de uma vez

### Frase para guardar
“Programar não é só escrever código; é entender problemas e transformar lógica em solução.”

---

## Aula 14 — Exercício final

Objetivo:
Fixar tudo que você aprendeu.

### Seu exercício
Escolha um fluxo do sistema e explique:
1. O que acontece quando o usuário faz login
2. O que acontece quando um livro é cadastrado
3. O que acontece quando um empréstimo é criado
4. Como o sistema identifica um aluno pelo QR

Se você fizer isso, você já estará pensando como um programador profissional.

---

## Plano de estudos recomendado

### Semana 1
- Aula 1 a 4

### Semana 2
- Aula 5 a 8

### Semana 3
- Aula 9 a 12

### Semana 4
- Aula 13 e 14

---

## Recomendação final

Para você evoluir de verdade, faça assim:
- leia um arquivo por vez
- escreva em português o que ele faz
- tente explicar para outra pessoa
- compare com o comportamento real do sistema

Isso é o que mais aproxima você do nível profissional.
