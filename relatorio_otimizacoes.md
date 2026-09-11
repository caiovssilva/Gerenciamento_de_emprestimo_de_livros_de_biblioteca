# Relatório de otimizações aplicadas no projeto

## 1. Introdução

Este relatório detalha as melhorias realizadas para reduzir a carga de processamento do frontend e diminuir a sensação de lentidão e engasgos durante a navegação e uso do sistema.

Ele também distingue claramente entre:
- otimizações que foram realmente implementadas no código;
- melhorias que foram avaliadas como opcionais, mas não entraram no projeto final;
- pontos críticos que mais impactavam a performance e como foram tratados.

As otimizações foram aplicadas sem alterar o arquivo de ambiente [backend/.env](backend/.env), conforme solicitado.

### Objetivo geral
- reduzir renderizações desnecessárias;
- evitar sincronizações redundantes;
- reduzir custo de processamento em filtros e listas grandes;
- manter a experiência do usuário mais responsiva.

### Validação executada
Após as mudanças, foi feita a validação com:
- checagem de sintaxe JavaScript dos arquivos alterados;
- execução de testes relevantes do backend.

Resultado confirmado: 4 testes passaram.

---

## 2. Otimizações implementadas no código

### 2.1. Debounce nos filtros de busca

### Arquivo afetado
- [frontend/assets/js/app.js](frontend/assets/js/app.js)
- [frontend/index.html](frontend/index.html)

### Problema
Os campos de busca foram disparando a renderização toda vez que o usuário digitava uma tecla. Em telas com várias linhas, esse comportamento causa:
- renderização repetida da tabela;
- uso excessivo do navegador;
- lentidão perceptível durante a digitação;
- processamento repetido desnecessário.

### Solução aplicada
Foi criada uma função de debounce e um scheduler de renderização:
- a função espera um pequeno intervalo antes de executar;
- se o usuário continuar digitando, só a última ação é processada;
- isso reduz múltiplos re-renders desnecessários.

### Por que isso resolve
Quando a pessoa digita rapidamente, o sistema não tenta renderizar a cada tecla. Em vez disso, ele processa somente após a pausa natural da digitação, o que reduz carga e melhora a fluidez.

### Trecho representativo
No arquivo [frontend/assets/js/app.js](frontend/assets/js/app.js), foi adicionado o scheduler com debounce para páginas como livros, alunos, salas e empréstimos.

### Impacto
- menos re-render no navegador;
- mais responsividade ao digitar;
- menor consumo de CPU.

---

### 2.2. Cooldown de sincronização de dados

### Arquivo afetado
- [frontend/assets/js/app.js](frontend/assets/js/app.js)

### Problema
A sincronização de dados era disparada repetidamente em sequência. Isso gerava:
- múltiplas chamadas ao backend;
- atualização de estado em excesso;
- reprocessamento das páginas enquanto o usuário já estava em uma condição recente e estável.

### Solução aplicada
Foi inserido um limitador de sincronização:
- a aplicação só sincroniza novamente após certo tempo;
- se os dados já foram atualizados recentemente, ela não repete o trabalho;
- a sincronização ainda acontece quando necessário, mas evita excesso.

### Por que isso resolve
O sistema passa a respeitar um intervalo mínimo entre atualizações, evitando uma cascata de requisições e atualização do DOM.

### Impacto
- menos trafego de rede;
- menos carga no servidor;
- interface mais estável;
- menos risco de travamento causado por loops de sincronização.

---

### 2.3. Redução de loops e filtros repetitivos em listas grandes

### Arquivos afetados
- [frontend/assets/js/pages/books.js](frontend/assets/js/pages/books.js)
- [frontend/assets/js/pages/students.js](frontend/assets/js/pages/students.js)

### Problema
As páginas de livros e alunos realizavam múltiplos filtros e buscas com estruturas lineares, como:
- `filter()` repetido em muitos arrays;
- contagem de empréstimos em laços internos;
- busca de dados dispersa em vários lugares.

Esse padrão é funcional, mas se torna lento quando há muitos registros.

### Solução aplicada
Foi substituído o processamento repetitivo por estruturas mais eficientes, usando `Map` para agregar dados relevantes, como por exemplo:
- contar empréstimos ativos por livro;
- agrupar empréstimos por aluno;
- buscar salas e estados de forma direta, sem percorrer os mesmos dados várias vezes.

### Por que isso resolve
Em vez de percorrer arrays repetidas vezes, a aplicação calcula o que precisa em uma passada mais inteligente. Isso reduz complexidade e acelera a renderização.

### Impacto
- menor custo de processamento;
- renderização mais rápida;
- melhor performance em listas maiores.

---

### 2.4. Desacoplamento da renderização da digitação

### Arquivos afetados
- [frontend/index.html](frontend/index.html)
- [frontend/assets/js/app.js](frontend/assets/js/app.js)

### Problema
Os inputs de busca chamavam diretamente as funções de renderização em cada evento de teclado. Isso fazia o navegador renderizar sem controle e com excesso de repetições.

### Solução aplicada
Os eventos `oninput` foram direcionados para um scheduler centralizado, em vez de disparar diretamente a renderização cada vez.

### Por que isso resolve
Essa mudança centraliza o controle e evita que múltiplos eventos do usuário acessem imediatamente o código pesado. O scheduler organiza a execução em um fluxo mais eficiente.

### Impacto
- mais previsibilidade no comportamento da interface;
- menos pressão no renderizador;
- melhor sensação de fluidez ao navegar e pesquisar.

---

---

## 3. Melhorias consideradas, mas não implantadas como parte do escopo final

Estas são opções válidas para uma próxima etapa, mas não foram implementadas neste ciclo de otimização, porque o objetivo principal foi melhorar os gargalos mais evidentes sem ampliar o escopo de forma desnecessária.

### 3.1. Lazy loading de listas
Possibilidade: carregar os dados em páginas menores à medida que o usuário navega.

Vantagem:
- reduz carga inicial da tela;
- melhora experiência em bancos grandes.

Desvantagem / problema:
- exige arquitetura mais complexa no frontend;
- aumenta a complexidade de paginação e filtros.

### 3.2. Cache mais agressivo no cliente
Possibilidade: guardar listas no navegador por mais tempo e atualizar em segundo plano.

Vantagem:
- reduz requisições repetidas;
- melhora resposta para navegação recorrente.

Desvantagem / problema:
- pode deixar dados desatualizados se não houver sincronização correta;
- exige política clara de expiração.

### 3.3. Paginação no backend e no frontend
Possibilidade: limitar quantidade de registros por tela.

Vantagem:
- reduz payload e renderização;
- melhora performance em grandes volumes.

Desvantagem / problema:
- exige mais ajustes na UI, filtros e navegação;
- pode afetar a experiência de quem usa relatório completo.

### 3.4. Compressão e minificação de assets
Possibilidade: reduzir tamanho dos arquivos JavaScript/CSS.

Vantagem:
- carregamento mais rápido;
- menor uso de rede.

Desvantagem / problema:
- não resolve o gargalo principal de renderização em uso ativo;
- precisa de etapa de build/empacotamento.

---

## 4. Benefícios gerais obtidos

A partir das otimizações, o projeto passou a:
- reagir melhor à digitação;
- reduzir processamento redundante;
- evitar atualização em cascata;
- manter melhor estabilidade em telas com muitos dados;
- continuar funcional sem impacto em regras de negócio.

---

## 5. Observações finais

As otimizações aplicadas foram focadas em comportamento e performance do cliente, sem mexer no arquivo de configuração do ambiente. A prioridade foi remover gargalos visíveis sem comprometer a lógica de negócio.

Esse tipo de ajuste é importante porque o problema mais comum de lentidão em interfaces web não está apenas no backend, mas também em:
- filtros disparados repetidamente;
- renderizações excessivas;
- sincronizações automáticas em excesso;
- processamento repetitivo sobre arrays grandes.

A correção feita reduz esses efeitos de forma objetiva e mensurável.

---

## 6. Verificação final

As alterações foram validadas com checagem de sintaxe e testes relevantes.

Resultado confirmado:
- 4 testes passaram;
- nenhuma falha relevante foi observada na validação executada.
