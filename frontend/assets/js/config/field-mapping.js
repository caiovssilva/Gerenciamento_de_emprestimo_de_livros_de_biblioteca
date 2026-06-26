/**
 * assets/js/config/field-mapping.js
 * Mapeia nomes de campos entre diferentes fontes (backend, frontend, JSON local)
 * Centraliza convenções de nomenclatura para evitar inconsistências
 */

const FIELD_MAPPING = {
  // Livros
  books: {
    canonical: {
      id: 'id',
      title: 'titulo',        // Backend usa português
      author: 'autor',
      isbn: 'isbn',
      area: 'area',
      copies: 'exemplares',   // Backend usa português
      genre_id: 'genero_id',  // Backend usa português
      created_at: 'created_at',
    },
    aliases: {
      title: ['titulo', 'title'],
      author: ['autor', 'author'],
      copies: ['exemplares', 'copies'],
      genre_id: ['genero_id', 'genre_id'],
    }
  },

  // Alunos
  students: {
    canonical: {
      id: 'id',
      name: 'nome',          // Backend usa português
      class: 'turma',        // Backend usa português
      card: 'carteirinha',   // Backend usa português
      room_id: 'sala_id',
      is_librarian: 'is_librarian',
      created_at: 'created_at',
    },
    aliases: {
      name: ['nome', 'name'],
      class: ['turma', 'class'],
      card: ['carteirinha', 'card'],
      room_id: ['sala_id', 'room_id'],
    }
  },

  // Empréstimos
  loans: {
    canonical: {
      id: 'id',
      book_id: 'livro_id',
      student_id: 'aluno_id',
      exemplar: 'exemplar',
      borrowed_at: 'data_emprestimo',
      due_date: 'data_devolucao_prevista',
      returned_at: 'devolvido_em',
      status: 'status',
    },
    aliases: {
      borrowed_at: ['data_emprestimo', 'borrowed_at'],
      due_date: ['data_devolucao_prevista', 'due_date'],
      returned_at: ['devolvido_em', 'returned_at'],
    }
  },

  // Salas
  rooms: {
    canonical: {
      id: 'id',
      name: 'nome',
      code: 'codigo',
    },
    aliases: {
      name: ['nome', 'name'],
      code: ['codigo', 'code'],
    }
  },

  // Gêneros
  genres: {
    canonical: {
      id: 'id',
      name: 'nome',
      color: 'cor',
      icon: 'icone',
    },
    aliases: {
      name: ['nome', 'name'],
      color: ['cor', 'color'],
      icon: ['icone', 'icon'],
    }
  }
};

/**
 * Normaliza um objeto usando o mapeamento de campos
 * @param {Object} data - Dados a normalizar
 * @param {String} type - Tipo ('books', 'students', 'loans', 'rooms', 'genres')
 * @returns {Object} - Dados normalizados
 */
function normalizeFields(data, type) {
  if (!FIELD_MAPPING[type]) {
    console.warn(`Tipo desconhecido para normalização: ${type}`);
    return data;
  }

  const mapping = FIELD_MAPPING[type];
  const normalized = {};

  // Copia todos os campos originais
  Object.assign(normalized, data);

  // Aplica aliases
  Object.entries(mapping.aliases || {}).forEach(([canonical, aliases]) => {
    const value = aliases.reduce((val, alias) => val !== undefined ? val : data[alias], undefined);
    if (value !== undefined && !normalized[canonical]) {
      normalized[canonical] = value;
    }
  });

  return normalized;
}

// Export para uso global
if (typeof window !== 'undefined') {
  window.FIELD_MAPPING = FIELD_MAPPING;
  window.normalizeFields = normalizeFields;
}
