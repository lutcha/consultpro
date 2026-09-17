// ============================================
// TERMS OF USE — DRAFT for legal review
// ============================================

import { Link } from 'react-router-dom';
import { LegalPageLayout } from '@/components/layout/LegalPageLayout';

export function Terms() {
  return (
    <LegalPageLayout title="Termos de Utilização">
      <section>
        <h2>1. Introdução</h2>
        <p>
          Estes Termos de Utilização regem o acesso e uso da plataforma ConsultPro
          (<strong>"ConsultPro"</strong>, <strong>"a Plataforma"</strong>), disponível em{' '}
          <a href="https://consultpro.cv">consultpro.cv</a>, operada por [Nome legal da
          empresa a confirmar] ("nós", "a Empresa"), com sede em Praia, Cabo Verde.
        </p>
        <p>
          Ao criar uma conta ou utilizar a Plataforma, aceitas estes Termos. Se não
          concordares, não deves utilizar o serviço.
        </p>
      </section>

      <section>
        <h2>2. Descrição do serviço</h2>
        <p>
          A ConsultPro é uma plataforma SaaS que apoia empresas de consultoria, ONGs e
          organizações similares a identificar, avaliar e responder a oportunidades de
          projeto financiadas (concursos, editais, RFPs), incluindo agregação de fontes de
          oportunidades, pontuação estratégica, montagem de equipas e CVs, controlo de
          qualidade de propostas e exportação de submissões.
        </p>
        <p>
          <strong>Fase atual: Beta controlado.</strong> A Plataforma está em fase de beta,
          com acesso por convite a um número limitado de organizações. Funcionalidades
          podem mudar, ter limitações, ou ser descontinuadas sem aviso prévio equivalente
          ao de um produto em produção estável. Não garantimos disponibilidade
          ininterrupta nem cobertura completa de todas as fontes de oportunidades.
        </p>
      </section>

      <section>
        <h2>3. Contas e elegibilidade</h2>
        <p>
          Precisas de criar uma conta para usar a Plataforma. És responsável por manter a
          confidencialidade das tuas credenciais e por toda a atividade realizada através
          da tua conta. Deves fornecer informação verdadeira e mantê-la atualizada.
        </p>
        <p>
          Cada organização ("tenant") gere os seus próprios membros e permissões dentro da
          Plataforma. O administrador de cada organização é responsável por gerir o acesso
          da sua equipa.
        </p>
      </section>

      <section>
        <h2>4. Plano beta e preços</h2>
        <p>
          Durante o período de beta, o acesso é oferecido com um período experimental
          gratuito de 15 dias por organização convidada. Após esse período, condições
          comerciais serão comunicadas antecipadamente antes de qualquer cobrança. Não
          existe atualmente faturação automática nem recolha de dados de pagamento na
          Plataforma.
        </p>
      </section>

      <section>
        <h2>5. Utilização aceitável</h2>
        <p>Ao usar a Plataforma, comprometes-te a não:</p>
        <ul>
          <li>Usar o serviço para fins ilegais ou fraudulentos;</li>
          <li>Tentar aceder a dados de outras organizações (tenants) sem autorização;</li>
          <li>Fazer engenharia reversa, copiar ou revender a Plataforma sem autorização;</li>
          <li>Sobrecarregar a infraestrutura de forma intencional (scraping abusivo, automação não autorizada, etc.);</li>
          <li>Carregar conteúdo ilegal, difamatório ou que viole direitos de terceiros.</li>
        </ul>
      </section>

      <section>
        <h2>6. Conteúdo e propriedade intelectual</h2>
        <p>
          Mantens a propriedade de todo o conteúdo que carregas na Plataforma (CVs,
          propostas, documentos, dados de perfil). Concedes-nos uma licença limitada para
          armazenar, processar e exibir esse conteúdo exclusivamente para prestar o
          serviço à tua organização.
        </p>
        <p>
          O software, design, marca e demais elementos da Plataforma são propriedade da
          Empresa ou dos seus licenciadores.
        </p>
      </section>

      <section>
        <h2>7. Funcionalidades de Inteligência Artificial</h2>
        <p>
          A Plataforma pode usar modelos de IA (de terceiros ou próprios) para sugerir
          pontuações de oportunidades, refinamentos de perfil estratégico e apoio à
          redação de propostas. As sugestões de IA são um apoio à decisão — a Plataforma
          não altera silenciosamente a estratégia ou pesos de pontuação de uma
          organização sem ação explícita de um utilizador autorizado. É responsabilidade
          da organização rever e validar qualquer conteúdo gerado ou sugerido por IA
          antes de o usar em submissões oficiais.
        </p>
      </section>

      <section>
        <h2>8. Limitação de responsabilidade</h2>
        <p>
          A Plataforma é fornecida "tal como está", especialmente durante a fase beta. Na
          máxima medida permitida por lei, não somos responsáveis por perdas indiretas,
          lucros cessantes, ou danos resultantes de indisponibilidade do serviço, erros em
          fontes de oportunidades de terceiros, ou decisões tomadas com base em conteúdo
          gerado por IA.
        </p>
      </section>

      <section>
        <h2>9. Suspensão e cancelamento</h2>
        <p>
          Podemos suspender ou encerrar o acesso de uma organização em caso de violação
          destes Termos, uso indevido, ou não pagamento (quando aplicável). Uma
          organização pode solicitar o encerramento da sua conta e a eliminação dos seus
          dados a qualquer momento através do canal de suporte.
        </p>
      </section>

      <section>
        <h2>10. Alterações aos Termos</h2>
        <p>
          Podemos atualizar estes Termos periodicamente. Alterações materiais serão
          comunicadas através da Plataforma ou por email antes de entrarem em vigor.
        </p>
      </section>

      <section>
        <h2>11. Contacto</h2>
        <p>
          Para questões sobre estes Termos, contacta-nos através da{' '}
          <Link to="/support">página de suporte</Link> ou em{' '}
          <a href="mailto:info@consultpro.cv">info@consultpro.cv</a>.
        </p>
      </section>
    </LegalPageLayout>
  );
}
