# Arquitetura e escolhas técnicas

O DataPulse processa dados sintéticos da Atlas Commerce e serve resultados reais
por PostgreSQL, FastAPI e React. Bronze preserva strings originais e metadados de
origem e execução; Silver contém pedidos validados com joins de clientes/produtos;
Gold agrega vendas por região e categoria. Quarentena preserva o original e todas
as regras violadas. PostgreSQL registra execuções, regras, fatos, agregações e incidentes.

O hash SHA256 dos arquivos identifica o lote, enquanto UUID identifica cada tentativa.
Reexecutar o mesmo lote substitui seus resultados numa transação, sem duplicá-los.
Uma advisory lock do PostgreSQL bloqueia execuções concorrentes. O retry reclama
o incidente atomicamente, reutiliza a origem e a data de validação e só resolve o
incidente após uma execução bem-sucedida. Falhas retornam erro HTTP e são auditadas.

A API separa rotas, schemas, repositórios e serviços. O dashboard usa TanStack Query,
React e Recharts; não possui indicadores aleatórios. A chave administrativa é exigida
para execução, retry e consulta aos dados originais da quarentena. Credenciais ficam
no .env ignorado pelo Git; a chave do navegador permanece somente em memória.

Pandas oferece o fluxo local econômico. O perfil opcional PySpark utiliza DataFrames
para normalização, deduplicação, joins e agregação. Scala executa uma agregação
analítica independente no JVM e seu resultado Gold pode alimentar a persistência.
Airflow agenda chamadas à API com dependências, retry e timeout. Na DAG atual, as
etapas de dados são agrupadas numa tarefa atômica; retomada por etapa continua pendente.

O Python 3.12.9 e a .venv existentes foram preservados. PostgreSQL 16.6 e Docker
estão operacionais. A memória Docker identificada foi aproximadamente 1,8 GiB;
execute perfis avançados sequencialmente ou configure mais memória para combiná-los.
Consulte delivery-status.md para testes realmente executados. Código disponível não
é declaração de aprovação de testes. Retenção automática e recuperação de processos
interrompidos abruptamente ainda precisam ser implementadas.
