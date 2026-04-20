// ============================================
// PORTUGUESE TRANSLATIONS
// ============================================

export const pt = {
  common: {
    navigation: {
      dashboard: 'Dashboard',
      opportunities: 'Oportunidades',
      proposals: 'Propostas',
      teams: 'Equipas',
      settings: 'Definições',
      logout: 'Sair',
    },
    actions: {
      save: 'Guardar',
      submit: 'Submeter',
      cancel: 'Cancelar',
      edit: 'Editar',
      delete: 'Eliminar',
      create: 'Criar',
      view: 'Ver',
      download: 'Descarregar',
      upload: 'Carregar',
      search: 'Pesquisar',
      filter: 'Filtrar',
      export: 'Exportar',
      import: 'Importar',
      close: 'Fechar',
      back: 'Voltar',
      next: 'Próximo',
      previous: 'Anterior',
      confirm: 'Confirmar',
      apply: 'Aplicar',
      ignore: 'Ignorar',
      resolve: 'Resolver',
    },
    status: {
      draft: 'Rascunho',
      review: 'Em Revisão',
      submitted: 'Submetida',
      won: 'Ganha',
      lost: 'Não Aprovada',
      pending: 'Pendente',
      active: 'Ativo',
      inactive: 'Inativo',
    },
    labels: {
      loading: 'A carregar...',
      error: 'Erro',
      success: 'Sucesso',
      warning: 'Aviso',
      info: 'Informação',
      noData: 'Sem dados',
      searchPlaceholder: 'Pesquisar...',
      selectOption: 'Selecionar opção',
      all: 'Todos',
    },
  },
  dashboard: {
    title: 'Dashboard',
    welcome: 'Bem-vindo, {{name}}',
    weeklyReport: 'Relatório Semanal',
    kpis: {
      activeOpportunities: 'Oportunidades Ativas',
      proposalsInProgress: 'Propostas em Curso',
      winRate: 'Taxa de Vitória',
      upcomingDeadlines: 'Prazos Próximos',
    },
    pipeline: {
      title: 'Pipeline de Propostas',
      columns: {
        title: 'Título',
        client: 'Cliente',
        deadline: 'Prazo',
        status: 'Estado',
        actions: 'Ações',
      },
    },
    alerts: {
      title: 'Alertas Inteligentes',
    },
    activity: {
      title: 'Atividade Recente',
    },
  },
  opportunities: {
    title: 'Oportunidades',
    details: {
      title: 'Detalhes da Oportunidade',
      tabs: {
        summary: 'Resumo',
        tor: 'ToR',
        matrix: 'Matriz',
        risks: 'Riscos',
      },
      aiSummary: 'Resumo IA',
      requirements: {
        title: 'Requisitos Extraídos',
        categories: {
          functional: 'Funcionais',
          technical: 'Técnicos',
          institutional: 'Institucionais',
          financial: 'Financeiros',
        },
        validateAll: 'Validar Todos',
        export: 'Exportar CSV',
      },
      actions: {
        go: 'Go — Avançar com proposta',
        noGo: 'No-Go — Arquivar oportunidade',
        addNote: 'Adicionar nota interna',
      },
    },
  },
  proposals: {
    title: 'Propostas',
    editor: {
      title: 'Editor de Proposta',
      sections: {
        cover: 'Capa',
        executive_summary: 'Resumo Executivo',
        methodology: 'Metodologia',
        team: 'Equipa Técnica',
        workplan: 'Plano de Trabalho',
        budget: 'Orçamento',
        annexes: 'Anexos',
      },
      aiAssist: {
        title: 'Assistente IA',
        expand: 'Expandir parágrafo',
        summarize: 'Resumir para 100 palavras',
        toneFormal: 'Ajustar tom: mais formal',
        translateEN: 'Traduzir para EN',
      },
      sidebar: {
        requirements: 'Requisitos do ToR',
        checklist: 'Checklist de Conformidade',
        suggestions: 'Sugestões de IA',
      },
      footer: {
        draft: 'Rascunho',
        save: 'Guardar',
        submitQC: 'Submeter para QC',
      },
    },
    qc: {
      title: 'Quality Check',
      score: 'Pontuação',
      progress: 'Progresso',
      categories: {
        compliance: 'Conformidade com ToR',
        coherence: 'Coerência Narrativa',
        budget: 'Orçamento',
        attachments: 'Anexos',
      },
      actions: {
        rerun: 'Re-run QC',
        exportReport: 'Exportar Report',
        approve: 'Aprovar',
      },
      warnings: {
        minScore: 'Score < 85 bloqueia submissão',
      },
    },
  },
  landing: {
    hero: {
      title: 'Automatize as suas propostas de consultoria internacional',
      subtitle: 'Plataforma inteligente que acelera a criação, revisão e submissão de propostas para UN, Banco Mundial, UE e outros organismos.',
      ctaPrimary: 'Entrar na Plataforma',
      ctaSecondary: 'Ver demonstração',
    },
    features: {
      title: 'Funcionalidades',
      items: {
        aiAnalysis: {
          title: 'Análise IA de ToR',
          description: 'Extração automática de requisitos, riscos e critérios de avaliação em segundos.',
        },
        teamMatching: {
          title: 'Matching de Equipa',
          description: 'Encontre os consultores ideais com base em skills, experiência e disponibilidade.',
        },
        qualityCheck: {
          title: 'Quality Check Automático',
          description: 'Validação de conformidade com ToR e critérios QCBS antes da submissão.',
        },
      },
    },
    howItWorks: {
      title: 'Como Funciona',
      steps: {
        upload: {
          number: '1',
          title: 'Upload do ToR',
          description: 'Carregue o documento em PDF ou DOCX',
        },
        analysis: {
          number: '2',
          title: 'Análise IA',
          description: 'O sistema extrai requisitos e sugere estratégia',
        },
        proposal: {
          number: '3',
          title: 'Proposta Pronta',
          description: 'Gere documentos profissionais em minutos',
        },
      },
    },
  },
};
