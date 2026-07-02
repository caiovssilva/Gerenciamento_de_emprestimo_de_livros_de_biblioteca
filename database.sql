-- ============================================================
-- BIBLIOTECA narceu de paiva filho — Campus Aracruz v3
-- Execute no SQL Editor do Supabase
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Limpa objetos antigos
DROP VIEW  IF EXISTS vw_emprestimos_ativos CASCADE;
DROP VIEW  IF EXISTS vw_livros_ranking     CASCADE;
DROP TABLE IF EXISTS relatorios_mensais    CASCADE;
DROP TABLE IF EXISTS emprestimos           CASCADE;
DROP TABLE IF EXISTS livros                CASCADE;
DROP TABLE IF EXISTS alunos                CASCADE;
DROP TABLE IF EXISTS salas                 CASCADE;
DROP TABLE IF EXISTS generos               CASCADE;
DROP TABLE IF EXISTS usuarios              CASCADE;

-- ── 1. USUÁRIOS ──────────────────────────────────────────────
CREATE TABLE usuarios (
    id        UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome      VARCHAR(255) NOT NULL,
    login     VARCHAR(100) UNIQUE NOT NULL,
    senha     VARCHAR(255) NOT NULL,
    criado_em TIMESTAMP    DEFAULT NOW()
);
INSERT INTO usuarios (nome, login, senha) VALUES
    ('Administrador', 'admin',      'narceu2026'),
    ('Bibliotecária', 'biblioteca', 'narceu2026')
ON CONFLICT (login) DO NOTHING;

-- ── 2. SALAS ─────────────────────────────────────────────────
CREATE TABLE salas (
    id         UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome       VARCHAR(100) NOT NULL,
    codigo     VARCHAR(20)  DEFAULT '',
    descricao  TEXT         DEFAULT '',
    capacidade INT          DEFAULT 40,
    criado_em  TIMESTAMP    DEFAULT NOW()
);
CREATE INDEX idx_salas_codigo ON salas (codigo);

-- ── 3. GÊNEROS DE LIVRO ───────────────────────────────────────
CREATE TABLE generos (
    id        UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome      VARCHAR(80) NOT NULL,
    icone     VARCHAR(50) DEFAULT 'ti-book',
    cor       VARCHAR(20) DEFAULT '#6366f1',
    criado_em TIMESTAMP   DEFAULT NOW()
);
-- Gêneros padrão
INSERT INTO generos (nome, icone, cor) VALUES
    ('Técnico / Didático', 'ti-school',        '#1a4f8a'),
    ('Ficção Científica',  'ti-rocket',         '#7c3aed'),
    ('Romance',            'ti-heart',          '#e11d48'),
    ('Aventura',           'ti-sword',          '#d97706'),
    ('Comédia',            'ti-mood-happy',     '#16a34a'),
    ('Terror / Suspense',  'ti-ghost',          '#374151'),
    ('História',           'ti-history',        '#92400e'),
    ('Biografia',          'ti-user-star',      '#0369a1'),
    ('Autoajuda',          'ti-brain',          '#065f46'),
    ('Outros',             'ti-books',          '#64748b');

-- ── 4. LIVROS ─────────────────────────────────────────────────
CREATE TABLE livros (
    id         UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    isbn       VARCHAR(50)  DEFAULT '',
    titulo     VARCHAR(255) NOT NULL,
    autor      VARCHAR(255) NOT NULL DEFAULT '',
    area       VARCHAR(100) NOT NULL DEFAULT 'Geral',
    genero_id  UUID         REFERENCES generos(id) ON DELETE SET NULL,
    exemplares INT          NOT NULL DEFAULT 1 CHECK (exemplares >= 1),
    criado_em  TIMESTAMP    DEFAULT NOW()
);
CREATE INDEX idx_livros_isbn    ON livros (isbn)     WHERE isbn <> '';
CREATE INDEX idx_livros_titulo  ON livros (titulo);
CREATE INDEX idx_livros_area    ON livros (area);
CREATE INDEX idx_livros_genero  ON livros (genero_id);

-- ── 5. ALUNOS ────────────────────────────────────────────────
CREATE TABLE alunos (
    id          UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome        VARCHAR(255) NOT NULL,
    turma       VARCHAR(50)  NOT NULL DEFAULT '',
    carteirinha VARCHAR(100) DEFAULT '',
    sala_id     UUID         REFERENCES salas(id) ON DELETE SET NULL,
    criado_em   TIMESTAMP    DEFAULT NOW()
);
CREATE UNIQUE INDEX idx_alunos_carteirinha
    ON alunos (carteirinha)
    WHERE carteirinha IS NOT NULL AND carteirinha <> '';
CREATE INDEX idx_alunos_nome  ON alunos (nome);
CREATE INDEX idx_alunos_turma ON alunos (turma);
CREATE INDEX idx_alunos_sala  ON alunos (sala_id);

-- ── 6. EMPRÉSTIMOS ───────────────────────────────────────────
CREATE TABLE emprestimos (
    id                      UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    livro_id                UUID        NOT NULL REFERENCES livros(id)  ON DELETE CASCADE,
    aluno_id                UUID        NOT NULL REFERENCES alunos(id)  ON DELETE CASCADE,
    exemplar                VARCHAR(10) NOT NULL DEFAULT '001',
    data_emprestimo         DATE        NOT NULL,
    data_devolucao_prevista DATE        NOT NULL,
    devolvido_em            DATE        DEFAULT NULL,
    observacao              TEXT        DEFAULT '',
    criado_por              VARCHAR(100) DEFAULT 'system',
    criado_em               TIMESTAMP   DEFAULT NOW()
);
CREATE UNIQUE INDEX idx_exemplar_ativo
    ON emprestimos (livro_id, exemplar)
    WHERE devolvido_em IS NULL;
CREATE INDEX idx_emp_livro  ON emprestimos (livro_id);
CREATE INDEX idx_emp_aluno  ON emprestimos (aluno_id);
CREATE INDEX idx_emp_ativo  ON emprestimos (devolvido_em) WHERE devolvido_em IS NULL;
CREATE INDEX idx_emp_data   ON emprestimos (data_emprestimo DESC);

-- ── 7. RELATÓRIOS MENSAIS ────────────────────────────────────
CREATE TABLE relatorios_mensais (
    id                 UUID       PRIMARY KEY DEFAULT uuid_generate_v4(),
    mes_ano            VARCHAR(7) UNIQUE NOT NULL,
    total_emprestimos  INT        DEFAULT 0,
    total_devolucoes   INT        DEFAULT 0,
    total_atrasos      INT        DEFAULT 0,
    livros_mais_lidos  JSONB      DEFAULT '[]',
    turmas_mais_ativas JSONB      DEFAULT '[]',
    gerado_em          TIMESTAMP  DEFAULT NOW(),
    gerado_por         VARCHAR(100) DEFAULT 'system'
);

-- ── 8. RLS ───────────────────────────────────────────────────
ALTER TABLE salas              ENABLE ROW LEVEL SECURITY;
ALTER TABLE generos            ENABLE ROW LEVEL SECURITY;
ALTER TABLE livros             ENABLE ROW LEVEL SECURITY;
ALTER TABLE alunos             ENABLE ROW LEVEL SECURITY;
ALTER TABLE emprestimos        ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuarios           ENABLE ROW LEVEL SECURITY;
ALTER TABLE relatorios_mensais ENABLE ROW LEVEL SECURITY;

CREATE POLICY "salas_all"      ON salas              FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "generos_all"    ON generos            FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "livros_all"     ON livros             FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "alunos_all"     ON alunos             FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "emprestimos_all"ON emprestimos        FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "relatorios_all" ON relatorios_mensais FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "usuarios_sel"   ON usuarios           FOR SELECT USING (true);

-- ── 9. VIEWS ─────────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_emprestimos_ativos AS
SELECT e.id, a.nome AS aluno, a.turma, a.carteirinha,
       l.titulo AS livro, l.autor, l.area,
       g.nome AS genero,
       sa.nome AS sala,
       e.exemplar, e.data_emprestimo, e.data_devolucao_prevista,
       (CURRENT_DATE - e.data_devolucao_prevista) AS dias_atraso,
       CASE WHEN CURRENT_DATE > e.data_devolucao_prevista THEN 'atrasado'
            WHEN CURRENT_DATE = e.data_devolucao_prevista THEN 'vence_hoje'
            ELSE 'em_dia' END AS status
FROM emprestimos e
JOIN livros l  ON l.id  = e.livro_id
JOIN alunos a  ON a.id  = e.aluno_id
LEFT JOIN generos g ON g.id = l.genero_id
LEFT JOIN salas   sa ON sa.id = a.sala_id
WHERE e.devolvido_em IS NULL
ORDER BY e.data_devolucao_prevista;

CREATE OR REPLACE VIEW vw_livros_ranking AS
SELECT l.id, l.titulo, l.autor, l.area, l.isbn, l.exemplares,
       g.nome AS genero, g.cor AS genero_cor,
       COUNT(e.id) AS total_emprestimos,
       COUNT(e.id) FILTER (WHERE e.devolvido_em IS NULL) AS emprestados,
       l.exemplares - COUNT(e.id) FILTER (WHERE e.devolvido_em IS NULL) AS disponiveis
FROM livros l
LEFT JOIN emprestimos e ON e.livro_id = l.id
LEFT JOIN generos     g ON g.id = l.genero_id
GROUP BY l.id, g.nome, g.cor
ORDER BY total_emprestimos DESC;

-- ── 10. DADOS DE EXEMPLO ─────────────────────────────────────
-- Salas
INSERT INTO salas (nome, codigo, descricao, capacidade) VALUES
    ('Sala 1A', 'S1A', 'Primeiro ano turma A', 35),
    ('Sala 1B', 'S1B', 'Primeiro ano turma B', 35),
    ('Sala 2A', 'S2A', 'Segundo ano turma A', 35),
    ('Sala 3A', 'S3A', 'Terceiro ano turma A', 35),
    ('Laboratório de Informática', 'LAB-INFO', 'Sala de aula prática', 20)
ON CONFLICT DO NOTHING;

-- ── FIM ──────────────────────────────────────────────────────
-- Verificar: SELECT tablename FROM pg_tables WHERE schemaname = 'public';
