// ============================================
// PRIVACY POLICY — DRAFT for legal review
// ============================================

import { Link } from 'react-router-dom';
import { LegalPageLayout } from '@/components/layout/LegalPageLayout';

export function Privacy() {
  return (
    <LegalPageLayout title="Política de Privacidade">
      <section>
        <h2>1. Introdução</h2>
        <p>
          Esta Política de Privacidade explica como a ConsultPro ("nós") recolhe, usa e
          protege dados pessoais dos utilizadores da plataforma disponível em{' '}
          <a href="https://consultpro.cv">consultpro.cv</a>.
        </p>
      </section>

      <section>
        <h2>2. Dados que recolhemos</h2>
        <p>Recolhemos os seguintes tipos de dados:</p>
        <ul>
          <li>
            <strong>Dados de conta:</strong> nome, email, password (encriptada), função na
            organização.
          </li>
          <li>
            <strong>Dados de perfil profissional:</strong> CV, competências, experiência,
            certificações, disponibilidade — quando fornecidos voluntariamente para uso nas
            funcionalidades de montagem de equipas e propostas.
          </li>
          <li>
            <strong>Dados da organização (tenant):</strong> nome, setor, mercados de
            interesse, preferências estratégicas de deteção de oportunidades.
          </li>
          <li>
            <strong>Dados de utilização:</strong> logs técnicos, endereço IP, ações na
            plataforma, para fins de segurança e melhoria do serviço.
          </li>
          <li>
            <strong>Comunicações de suporte:</strong> mensagens enviadas através do
            formulário de contacto/suporte.
          </li>
        </ul>
      </section>

      <section>
        <h2>3. Para que usamos os dados</h2>
        <ul>
          <li>Prestar e operar o serviço (autenticação, onboarding, gestão de propostas);</li>
          <li>Enviar emails transacionais (convites, confirmações, notificações de conta);</li>
          <li>Sugerir pontuações de oportunidades e apoio de IA, com base no perfil estratégico da organização;</li>
          <li>Responder a pedidos de suporte;</li>
          <li>Garantir a segurança da plataforma e prevenir abuso (ex.: verificação anti-robô no registo);</li>
          <li>Cumprir obrigações legais aplicáveis.</li>
        </ul>
        <p>Não vendemos dados pessoais a terceiros.</p>
      </section>

      <section>
        <h2>4. Isolamento entre organizações</h2>
        <p>
          Os dados de cada organização (tenant) são logicamente isolados dos de outras
          organizações na plataforma. O acesso entre tenants é tecnicamente bloqueado e
          testado; nenhuma organização vê dados de outra através da aplicação.
        </p>
      </section>

      <section>
        <h2>5. Prestadores de serviços (subprocessadores)</h2>
        <p>Para operar a plataforma, partilhamos dados com prestadores de infraestrutura, estritamente para os fins abaixo:</p>
        <ul>
          <li><strong>DigitalOcean</strong> — alojamento da aplicação e base de dados;</li>
          <li><strong>Twilio SendGrid</strong> — envio de emails transacionais (convites, notificações);</li>
          <li><strong>Cloudflare (Turnstile)</strong> — verificação anti-robô no registo;</li>
          <li>
            <strong>Fornecedores de modelos de IA</strong> (ex.: OpenAI, Anthropic, DeepSeek,
            ou equivalentes, consoante a configuração ativa) — apenas para funcionalidades
            de sugestão/pontuação assistida por IA, quando ativamente utilizadas.
          </li>
        </ul>
        <p>
          Cada um destes prestadores está contratualmente vinculado a usar os dados apenas
          para prestar o respetivo serviço.
        </p>
      </section>

      <section>
        <h2>6. Retenção de dados</h2>
        <p>
          Mantemos os dados enquanto a conta da organização estiver ativa. Após o
          encerramento de uma conta, os dados são eliminados ou anonimizados num prazo
          razoável, exceto quando a retenção for exigida por lei.
        </p>
      </section>

      <section>
        <h2>7. Os teus direitos</h2>
        <p>Tens o direito de:</p>
        <ul>
          <li>Aceder aos dados pessoais que temos sobre ti;</li>
          <li>Solicitar a correção de dados incorretos;</li>
          <li>Solicitar a eliminação da tua conta e dados associados;</li>
          <li>Retirar consentimento para comunicações não essenciais, quando aplicável.</li>
        </ul>
        <p>
          Para exercer estes direitos, contacta-nos através da{' '}
          <Link to="/support">página de suporte</Link>.
        </p>
      </section>

      <section>
        <h2>8. Segurança</h2>
        <p>
          Usamos medidas técnicas razoáveis para proteger os dados (encriptação em
          trânsito via HTTPS, passwords com hash, isolamento entre organizações). Nenhum
          sistema é 100% seguro; se identificares uma vulnerabilidade, contacta-nos
          imediatamente através da página de suporte.
        </p>
      </section>

      <section>
        <h2>9. Alterações a esta Política</h2>
        <p>
          Podemos atualizar esta Política periodicamente. Alterações materiais serão
          comunicadas através da Plataforma ou por email antes de entrarem em vigor.
        </p>
      </section>

      <section>
        <h2>10. Contacto</h2>
        <p>
          Para questões sobre privacidade, contacta-nos através da{' '}
          <Link to="/support">página de suporte</Link> ou em{' '}
          <a href="mailto:info@consultpro.cv">info@consultpro.cv</a>.
        </p>
      </section>
    </LegalPageLayout>
  );
}
