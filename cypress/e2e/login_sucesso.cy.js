describe('Fluxo de Login - Projeto Tia Cássia', () => {
  it('Deve logar como tia_cassia e carregar a lista de alunos', () => {
    // Visita a página inicial de acesso
    cy.visit('http://127.0.0.1:8000/login/')

    // Preenche o formulário com o usuário que configuramos no Admin
    cy.get('input[name="username"]').type('tia_cassia')
    cy.get('input[name="password"]').type('12345678') // Use a senha que você definiu

    // Clica no botão Entrar que corrigimos
    cy.get('button[type="submit"]').click()

    // Valida se o sistema levou para a página de alunos conforme o settings.py
    cy.url().should('include', '/alunos/')
    
    // Confirma se o título da tabela apareceu corretamente
    cy.contains('Nossos Alunos').should('be.visible')
    
    // Garante que não apareceu a mensagem de "Nenhum aluno cadastrado" se houver dados
    // Ou apenas valida que a estrutura da página carregou
    cy.get('table').should('exist')
  })
})