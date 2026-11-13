AprovaAí — mapa de funcionalidades e serviços
necessários

1. Objetivo

Este documento reúne as funcionalidades necessárias para o produto completo da
AprovaAí, identifica os serviços de backend exigidos pelas telas e jornadas planejadas e
propõe sua divisão entre os integrantes. O documento não pressupõe que o backend já
esteja implementado.

O escopo principal considera três perfis: aluno, professor e administrador. O protótipo
atual usa dados locais no navegador; no produto completo, o backend e o banco de
dados serão a fonte de verdade.

Visão geral dos blocos funcionais

As funcionalidades abaixo estão agrupadas por domínio de negócio. Os serviços
indicados são módulos lógicos de um mesmo backend e não precisam ser
implementados como microsserviços independentes.

Bloco

Funcionalidad
es

Entregas principais

Serviços centrais

Identidade e perfis  F02–F06, F33  Cadastro, login, sessão,

autorização, solicitação de
professor e perfil.

IdentityService, SessionService, ProfileService,
TeacherApplicationService

Catálogo e
descoberta

Comercial e
acesso

F01, F07–F10  Landing page, catálogo,

busca, detalhes e
recomendações.

F11–F15, F42  Matrícula, compra,

Vídeo e núcleo da
aprendizagem

F16–F20,
F34, F37–F38

Biblioteca,
interação e
comunicação

Gestão de cursos
e materiais

Administração e
análise

F21–F26,
F29–F32

F27,
F35–F36,
F39–F40

F28, F41,
F43–F46

assinatura, cancelamento,
direitos de acesso e
monetização.

Home, Meus Cursos,
página do curso, upload,
armazenamento, entrega
protegida de vídeo sob
demanda, reprodução,
progresso e certificado.

Histórico, favoritos,
playlists, anotações,
comentários, avaliações,
dúvidas e notificações.

Criação de cursos,
materiais complementares,
prévia e publicação.

Denúncias, métricas,
dashboard, aprovação de
professores, moderação e
auditoria.

CatalogService, SearchService,
RecommendationService, CourseService

PlanService, CheckoutService, PaymentService,
SubscriptionService, EnrollmentAccessService,
MonetizationService

LearningDashboardService, LessonPlaybackService,
ProgressService, LessonManagementService,
MediaService, CertificateService

StudyLibraryService, LessonInteractionService,
QuestionService, NotificationService

TeacherCourseDashboardService, CourseService,
CoursePublishingService, MaterialService

ReportService, TeacherAnalyticsService,
AdminDashboardService, TeacherModerationService,
ContentModerationService, AuditService

Divisão recomendada — 5 pessoas

Esta opção separa identidade, comércio, gestão de cursos e engajamento,
enquanto reúne a cadeia de vídeo e aprendizagem sob uma responsabilidade
ponta a ponta. Cada um dos 33 serviços de backend está atribuído a um único
grupo. A numeração identifica grupos de responsabilidade, não integrantes
específicos.

Grupo

Responsabilidade

Funcionalidades

Serviços atribuídos

Renan – Identidade e governança

F02–F06, F33, F44, F46

IdentityService, SessionService,
ProfileService, TeacherApplicationService,
TeacherModerationService, AuditService

Gustavo — Vídeo e núcleo da
aprendizagem

F16–F20, F34, F37–F38  LearningDashboardService,

João Carvalho - Comercial, acesso
e monetização

F11–F15, F42

Lucas – Catálogo e gestão de
cursos

F01, F07–F10, F27,
F35–F36, F39–F40

Daniel – Biblioteca, engajamento,
análise e moderação

F21–F26, F28–F32,
F41, F43, F45

Critérios para fechar a divisão

LessonPlaybackService, ProgressService,
LessonManagementService, MediaService,
CertificateService

PlanService, CheckoutService,
PaymentService, SubscriptionService,
EnrollmentAccessService,
MonetizationService

CatalogService, SearchService,
RecommendationService, CourseService,
CoursePublishingService, MaterialService,
TeacherCourseDashboardService

StudyLibraryService,
LessonInteractionService,
QuestionService, NotificationService,
ReportService, TeacherAnalyticsService,
AdminDashboardService,
ContentModerationService

1

2

3

4

5

A divisão em cinco pessoas é a recomendada porque preserva uma frente ponta a
ponta de vídeo e aprendizagem sem concentrar identidade, pagamentos e
moderação na mesma responsabilidade.
Manter upload, armazenamento, entrega protegida de vídeo sob demanda,

○
reprodução e progresso no mesmo grupo.
○
○
aprendizagem, interação e indicadores.

Tratar integrações entre grupos como contratos de API claramente definidos.
Planejar primeiro identidade, cursos e direitos de acesso; depois conectar

Mapa das telas — vídeo e núcleo da aprendizagem

O mapa abaixo relaciona a jornada ponta a ponta de vídeo e aprendizagem com as
telas, funcionalidades, serviços próprios e dependências de outros grupos.

Tela e ator

Responsabilidade

Funções

Serviços próprios e dependências

Home — aluno

Aula atual, progresso e continuar
assistindo.

F16, F20

Meus Cursos — aluno

Cursos, progresso e próxima aula.

F17, F20

Curso — aluno

Módulos, aulas, conclusão e próxima
aula.

F18, F20

Videoaula — aluno

Entrega protegida do vídeo,
navegação e salvamento da posição.

F19, F20

Certificado — aluno

Verificar conclusão e disponibilizar
certificado.

Gestão de aulas —
professor

Criar, editar, excluir e reordenar
aulas.

F34

F37

Edição da aula —
professor

Alterar dados, vídeo e thumbnail.

F37, F38

Upload de vídeo —
professor

Enviar arquivo e acompanhar
armazenamento e processamento.

Thumbnail — professor

Enviar, trocar ou remover a imagem
da aula.

F38

F38

Prévia da videoaula —
professor

Conferir vídeo e informações como
serão vistos pelo aluno.

F19, F37,
F38

Próprios: LearningDashboardService,
ProgressService e MediaService.
Dependências: IdentityService e
EnrollmentAccessService.

Próprios: LearningDashboardService e
ProgressService. Dependências:
EnrollmentAccessService e CourseService.

Próprios: LessonPlaybackService e
ProgressService. Dependências:
CourseService e EnrollmentAccessService.

Próprios: LessonPlaybackService,
MediaService e ProgressService.
Dependência: EnrollmentAccessService.

Próprios: CertificateService e
ProgressService. Dependências:
CourseService e NotificationService.

Próprio: LessonManagementService.
Dependências: CourseService e
autorização.

Próprios: LessonManagementService e
MediaService. Dependência:
CourseService.

Próprio: MediaService. Dependência:
armazenamento de arquivos.

Próprio: MediaService. Dependência:
armazenamento de arquivos.

Próprios: LessonPlaybackService,
MediaService e
LessonManagementService. Dependência:
CourseService.

Catálogo detalhado das funcionalidades

As seções seguintes descrevem individualmente cada funcionalidade e os serviços
necessários.

2. Acesso público e contas

F01 — Consultar a landing page

●  Apresentar a proposta da plataforma.

●  Mostrar uma amostra dos cursos publicados.

●  Oferecer entrada e criação de conta.

●  Não exigir autenticação.

Serviços necessários: CatalogService e, opcionalmente, RecommendationService.

F02 — Cadastrar aluno

●  Receber dados obrigatórios.

●  Validar e-mail único e senha.

●  Criar usuário com papel de aluno.

●  Iniciar sessão ou direcionar para o login.

Serviços necessários: IdentityService e ProfileService.

F03 — Entrar e sair

●  Autenticar usuário.

●  Criar sessão segura.

●  Identificar o papel do usuário.

●  Direcionar aluno, professor e administrador para suas áreas.

●  Encerrar e invalidar a sessão.

Serviços necessários: IdentityService e SessionService.

F04 — Recuperar acesso

●  Solicitar recuperação por e-mail.

●  Gerar código ou link com validade limitada.

●  Permitir definição de nova senha.

●  Invalidar o código depois do uso.

Serviços necessários: IdentityService e NotificationService.

F05 — Solicitar cadastro como professor

●  Receber dados pessoais e profissionais.

●  Receber documentos comprobatórios.

●  Registrar a solicitação como pendente.

●  Permitir consultar o estado da análise.

Serviços necessários: TeacherApplicationService, MediaService e NotificationService.

F06 — Autorizar ações por perfil

●  Restringir funções conforme o papel do usuário.

●  Garantir que um professor altere apenas seus próprios cursos.

●  Garantir que dados privados pertençam ao aluno autenticado.

●  Proteger funções administrativas.

Serviços necessários: IdentityService e políticas de autorização aplicadas em todos os

módulos.

3. Descoberta de cursos

F07 — Explorar cursos

●  Listar somente cursos publicados.

●  Filtrar por matéria, área e vestibular.

●  Ordenar por relevância, avaliação ou título.

●  Paginar resultados quando necessário.

Serviços necessários: CatalogService.

F08 — Pesquisar conteúdos

●  Pesquisar cursos, professores e materiais.

●  Normalizar acentos e variações de texto.

●  Combinar termo de busca e filtros.

●  Apresentar estado sem resultados.

Serviços necessários: SearchService, CatalogService e MaterialService.

F09 — Consultar detalhes de um curso

●  Mostrar descrição, professor, ementa e público-alvo.

●  Mostrar quantidade e duração das aulas.

●  Mostrar avaliação, preço e forma de acesso.

●  Identificar se o aluno já possui acesso.

●  Impedir nova compra do mesmo curso.

Serviços necessários: CourseService, EnrollmentAccessService e PlanService.

F10 — Recomendar cursos

●  Recomendar apenas cursos publicados e disponíveis.

●  Não recomendar novamente o curso que o aluno já está estudando.

●  Começar com critérios simples, como matéria, vestibular e popularidade.

●  Permitir evolução futura para personalização por histórico.

Serviços necessários: RecommendationService, CatalogService e
EnrollmentAccessService.

4. Aquisição e direito de acesso

F11 — Adicionar curso gratuito

●  Confirmar a matrícula gratuita.

●  Impedir matrículas duplicadas.

●  Liberar acesso às aulas permitidas.

Serviços necessários: EnrollmentAccessService.

F12 — Comprar curso individual

●  Criar uma intenção de compra.

●  Mostrar o resumo e o valor.

●  Confirmar ou rejeitar pagamento.

●  Liberar acesso somente depois da confirmação.

●  Impedir a compra repetida de um curso já adquirido.

Serviços necessários: CheckoutService, PaymentService e EnrollmentAccessService.

F13 — Contratar assinatura

●  Listar planos disponíveis.

●  Criar assinatura mensal ou anual conforme a regra definida.

●  Liberar os cursos incluídos no plano.

●  Mostrar situação, valor e próxima cobrança.

Serviços necessários: PlanService, SubscriptionService, PaymentService e
EnrollmentAccessService.

F14 — Cancelar assinatura

●  Solicitar e confirmar cancelamento.

●  Registrar quando o acesso termina.

●  Manter compras individuais independentes da assinatura.

●  Impedir cobranças posteriores indevidas.

Serviços necessários: SubscriptionService, PaymentService e EnrollmentAccessService.

F15 — Consultar acessos

●  Listar matrículas e direitos válidos do aluno.

●  Diferenciar curso gratuito, compra individual e assinatura.

●  Não mostrar como disponível um acesso expirado ou revogado.

Serviços necessários: EnrollmentAccessService.

5. Aprendizagem do aluno

F16 — Montar a Home do aluno

●  Mostrar curso em andamento.

●  Mostrar aula atual e progresso.

●  Permitir continuar a aula clicando no card principal.

●  Mostrar aulas anterior e seguinte.

●  Apresentar recomendações e avisos relevantes.

Serviços necessários: LearningDashboardService, ProgressService,
RecommendationService e NotificationService.

F17 — Consultar Meus Cursos

●  Listar cursos em andamento e concluídos.

●  Mostrar progresso e próxima aula.

●  Distinguir acesso válido, expirado ou bloqueado.

●  Direcionar para a página interna do curso.

Serviços necessários: EnrollmentAccessService e ProgressService.

F18 — Consultar a página interna do curso

●  Mostrar os módulos e todas as aulas.

●  Identificar aulas concluídas, atual e seguintes.

●  Permitir continuar da aula atual.

●  Oferecer caminho para dúvida geral sobre o curso.

Serviços necessários: LessonPlaybackService, ProgressService e QuestionService.

F19 — Assistir a uma videoaula

●  Verificar acesso antes de entregar a aula.

●  Obter vídeo, thumbnail, descrição e materiais.

●  Permitir navegar para aula anterior ou seguinte.

●  Exibir o contexto correto quando a aula vier de uma playlist.

●  Informar mídia indisponível sem perder os demais dados da aula.

Serviços necessários: LessonPlaybackService, MediaService, EnrollmentAccessService e
MaterialService.

F20 — Retomar e registrar progresso

●  Recuperar a última posição assistida.

●  Atualizar posição periodicamente ou ao sair.

●  Marcar aula como concluída conforme regra definida.

●  Calcular o progresso total do curso.

●  Impedir posição negativa ou maior que a duração.

Serviços necessários: ProgressService.

F21 — Consultar histórico

●  Registrar aulas abertas ou assistidas.

●  Ordenar pelas visualizações mais recentes.

●  Permitir retornar à aula.

Serviços necessários: StudyLibraryService.

F22 — Gerenciar favoritos

●  Adicionar ou remover uma aula dos favoritos.

●  Impedir duplicação.

●  Listar favoritos do aluno autenticado.

Serviços necessários: StudyLibraryService.

F23 — Gerenciar playlists

●  Criar, renomear e excluir playlists privadas.

●  Adicionar, remover e reordenar aulas.

●  Reproduzir a sequência dentro do contexto da playlist.

Serviços necessários: StudyLibraryService e LessonPlaybackService.

F24 — Criar anotações privadas

●  Criar e editar anotações vinculadas à aula.

●  Garantir que somente o aluno proprietário tenha acesso.

●  Recuperar as anotações ao reabrir a aula.

Serviços necessários: LessonInteractionService.

F25 — Comentar uma aula

●  Publicar comentário público vinculado à aula.

●  Identificar autor e horário.

●  Permitir resposta conforme a política definida.

●  Respeitar estado de moderação.

Serviços necessários: LessonInteractionService, ContentModerationService e
NotificationService.

F26 — Avaliar uma aula ou curso

●  Registrar uma avaliação por aluno e conteúdo.

●  Permitir atualização da avaliação.

●  Calcular média e quantidade de avaliações.

Serviços necessários: LessonInteractionService e TeacherAnalyticsService.

F27 — Consultar materiais complementares

●  Listar materiais do curso ou da aula.

●  Mostrar tipo, descrição e condição de acesso.

●  Gerar download autorizado.

●  Informar como obter acesso quando o material estiver bloqueado.

Serviços necessários: MaterialService e EnrollmentAccessService.

F28 — Enviar denúncia

●  Denunciar aula, curso ou comentário.

●  Registrar motivo e autor da denúncia.

●  Impedir duplicação indevida.

●  Colocar o item na fila de moderação.

Serviços necessários: ReportService e ContentModerationService.

6. Dúvidas e comunicação

F29 — Enviar dúvida

●  Enviar dúvida geral sobre um curso ou específica sobre uma aula.

●  Manter a dúvida privada entre aluno e professor responsável.

●  Registrar o estado como pendente.

Serviços necessários: QuestionService e NotificationService.

F30 — Acompanhar dúvida

●  Listar dúvidas enviadas.

●  Mostrar estado e resposta.

●  Manter o vínculo com curso e aula.

Serviços necessários: QuestionService.

F31 — Responder dúvida

●  Listar dúvidas destinadas ao professor.

●  Filtrar pendentes e respondidas.

●  Registrar resposta e data.

●  Notificar o aluno.

Serviços necessários: QuestionService e NotificationService.

F32 — Consultar notificações

●  Listar avisos do usuário.

●  Marcar aviso como lido.

●  Direcionar para aula, dúvida, certificado ou decisão relacionada.

Serviços necessários: NotificationService.

7. Perfil e conclusão

F33 — Consultar e editar perfil

●  Consultar dados pessoais.

●  Alterar nomes de exibição, preferências e avatar.

●  Validar dados antes de salvar.

●  Proteger campos que não podem ser alterados diretamente.

Serviços necessários: ProfileService e MediaService.

F34 — Emitir certificado

●  Verificar a regra de conclusão do curso.

●  Impedir emissão sem elegibilidade.

●  Registrar certificado único e verificável.

●  Permitir consulta e download.

Serviços necessários: CertificateService, ProgressService e NotificationService.

8. Gestão do professor

F35 — Consultar cursos do professor

●  Listar somente os cursos pertencentes ao professor autenticado.

●  Distinguir rascunhos e publicados.

●  Mostrar quantidade de aulas e alunos.

Serviços necessários: TeacherCourseDashboardService, CourseService e
EnrollmentAccessService.

F36 — Criar e editar curso

●  Criar rascunho.

●  Editar título, descrição, matéria, vestibulares e preço.

●  Definir acesso gratuito ou pago.

●  Salvar alterações sem publicar imediatamente.

Serviços necessários: CourseService.

F37 — Gerenciar aulas

●  Criar, editar e excluir aulas.

●  Reordenar aulas.

●  Vincular título, duração, descrição, vídeo e thumbnail.

●  Impedir alteração por professor que não seja proprietário do curso.

Serviços necessários: LessonManagementService e MediaService.

F38 — Enviar vídeos e thumbnails

●  Validar tipo e tamanho do arquivo.

●  Gerar upload autorizado.

●  Registrar metadados no banco.

●  Permitir trocar ou remover a thumbnail.

●  Usar uma imagem padrão quando não houver thumbnail personalizada.

Serviços necessários: MediaService.

F39 — Gerenciar materiais do curso

●  Enviar, editar e excluir materiais.

●  Vincular material ao curso ou à aula.

●  Definir formato e regra de acesso.

Serviços necessários: MaterialService e MediaService.

F40 — Visualizar prévia e publicar curso

●  Mostrar uma prévia antes da publicação.

●  Validar os campos obrigatórios.

●  Publicar somente cursos válidos.

●  Permitir retirar um curso de publicação conforme a regra definida.

Serviços necessários: CoursePublishingService, CourseService,
LessonManagementService e MaterialService.

F41 — Consultar métricas do professor

●  Mostrar matrículas, alunos ativos, conclusão e avaliações.

●  Filtrar por período e curso.

●  Identificar claramente a origem dos indicadores.

Serviços necessários: TeacherAnalyticsService.

F42 — Consultar monetização

●  Mostrar receita por curso.

●  Mostrar saldo, repasses e histórico.

●  Diferenciar cursos gratuitos e pagos.

●  Considerar somente receitas pertencentes ao professor autenticado.

Serviços necessários: MonetizationService, PaymentService e TeacherAnalyticsService.

9. Administração e moderação

F43 — Consultar dashboard administrativo

●  Mostrar quantidade de usuários, professores e cursos.

●  Mostrar acessos e atividade por período.

●  Permitir alternar o período dos indicadores.

Serviços necessários: AdminDashboardService.

F44 — Analisar solicitação de professor

●  Listar solicitações pendentes.

●  Consultar dados e documentos.

●  Aprovar ou rejeitar com motivo.

●  Atualizar o papel do usuário quando aprovado.

●  Notificar o solicitante.

Serviços necessários: TeacherModerationService, TeacherApplicationService,
IdentityService, AuditService e NotificationService.

F45 — Moderar conteúdo e comentários

●  Listar denúncias pendentes.

●  Consultar conteúdo, autor e motivo.

●  Manter, ocultar ou excluir o item.

●  Registrar decisão, responsável, data e justificativa.

Serviços necessários: ContentModerationService, ReportService e AuditService.

F46 — Manter trilha de auditoria

●  Registrar decisões administrativas e alterações sensíveis.

●  Preservar o estado anterior e o novo estado quando necessário.

●  Permitir consulta por usuário, entidade e período.

Serviços necessários: AuditService.

10. Serviços de backend identificados

Os nomes abaixo representam objetos ou módulos lógicos dentro de um mesmo backend,
e não microsserviços independentes:

●  IdentityService

●  SessionService

●  ProfileService

●  TeacherApplicationService

●  CatalogService

●  SearchService

●  RecommendationService

●  CourseService

●  LessonManagementService

●  CoursePublishingService

●  MediaService

●  MaterialService

●  PlanService

●  CheckoutService

●  PaymentService

●  SubscriptionService

●  EnrollmentAccessService

●  LearningDashboardService

●  LessonPlaybackService

●  ProgressService

●  StudyLibraryService

●  LessonInteractionService

●  QuestionService

●  NotificationService

●  CertificateService

●  TeacherCourseDashboardService

●  TeacherAnalyticsService

●  MonetizationService

●  ReportService

●  TeacherModerationService

●  ContentModerationService

●  AdminDashboardService

●  AuditService

11. Regras gerais

●  Somente cursos publicados aparecem no catálogo.

●  O professor só pode alterar cursos que lhe pertencem.

●  O aluno só pode abrir conteúdo protegido quando possuir acesso válido.

●  Identificadores do usuário devem vir da sessão autenticada, não apenas da

requisição enviada pelo navegador.

●  Compras, matrículas, avaliações, favoritos e denúncias não devem ser duplicados

indevidamente.

●  Anotações e dúvidas privadas não podem ser expostas a outros alunos.

●  Arquivos ficam em armazenamento próprio; o banco mantém referências e

metadados.

●  Operações de pagamento e decisões administrativas devem ser idempotentes e

auditáveis.

●  Erros de upload, pagamento ou salvamento não devem ser apresentados como

sucesso.

12. Funcionalidades futuras

As seguintes funcionalidades aparecem na visão inicial do produto, mas não estão
detalhadas nas telas e nos três perfis principais:

●  Planos para instituições de ensino.

●  Gestão de alunos vinculados a uma instituição.

●  Contratação de aulas particulares.

●  Agenda e pagamento de aulas particulares.

●  Recomendação adaptativa baseada no ritmo de estudo.

●  Transcodificação, múltiplas resoluções e streaming adaptativo de vídeo.

●  Repasse financeiro real aos professores.

●  Envio real de e-mail, SMS e notificações push.

Esses itens devem permanecer no backlog até que seus atores, regras e telas sejam

definidos.


