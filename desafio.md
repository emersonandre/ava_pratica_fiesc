# FIESC SESI SENAI IEL CIESC
## Formulário padronizado
### Prova Prática: Case On-line
**FIESC - DIGED - Diretoria de Gestão de Pessoas e Desempenho**

**Processo Seletivo** | 02198/2026 Desenvolvedor Full Stack - Pleno - IA e Python | **Etapa** | Avaliação Prática - Estudo de Caso
--- | --- | --- | ---
**Entidade** | | **Data** | 

**Dados a serem preenchidos pelo Candidato(a):**
* **Nome Completo:** 
* **E-mail:** 
* **CPF:** 

---

Olá, candidato (a)!
Seja bem-vindo à etapa prática do processo seletivo 02198/2026 - Desenvolvedor Full Stack - Pleno - IA e Python.

**Informações Importantes:**
* A prova online poderá ser realizada de qualquer computador com acesso à internet;
* Você terá 72 horas para o desenvolvimento e envio da resolução;
* Você deve anexar a sua resolução no link disponibilizado por e-mail;
* O arquivo deve estar nomeado com seu nome completo;
* Nos dias 11, 12 e 13/08/2026 acontecerá a entrevista individual complementar, os horários serão disponibilizados via errata após a finalização do prazo de envio do estudo de caso; A comprovação dos conhecimentos, será realizada também na entrevista;
* A participação da entrevista está condicionada ao envio da resolução do estudo de caso;
* O estudo de caso não poderá ser realizada por celulares ou tablets;
* Não nos responsabilizamos por problemas de instabilidade de internet;
* O aceite na agenda reforça o consenso do candidato sobre os critérios de avaliação e participação;
* Critérios de Avaliação Prática: Planejamento e Organização, Comunicação e Interação, Criatividade e Inovação, Conhecimento Técnico, Análise e Síntese.

---

### 1. Contextualização
**Avaliação Prática Case online:**
A manutenção preditiva está revolucionando a forma como as indústrias gerenciam seus ativos e evitam falhas não planejadas. Por meio da utilização de técnicas de Aprendizado de Máquina (Machine Learning) e análise avançada de dados, a Inteligência Artificial permite prever necessidades de manutenção com base em indicadores de desempenho monitorados em tempo real.

Essa abordagem utiliza diferentes variáveis coletadas diretamente dos equipamentos em operação, possibilitando a identificação antecipada de anomalias e reduzindo custos associados a paradas inesperadas e falhas operacionais.

Hoje a indústria está preocupada em ir além. Com o avanço dos modelos de linguagem, não deseja-se apenas descobrir quando um equipamento vai falhar, mas sim o que deve ser feito para que essa falha seja corrigida. Denominamos esse tipo de manutenção de manutenção prescritiva.

Uma indústria de grande porte localizada no estado de Santa Catarina entrou em contato com o SENAI SC demonstrando interesse no desenvolvimento de um projeto completo de Manutenção Prescritiva aplicado às máquinas e equipamentos de seu chão de fábrica.

O projeto contempla o desenvolvimento de algoritmos capazes de consultar automaticamente os bancos de dados da empresa, analisar novos conjuntos de dados provenientes dos equipamentos monitorados e identificar registros históricos que apresentem comportamento semelhante ao padrão observado.

A partir dessa correlação, o sistema deverá localizar ocorrências passadas com características próximas às do equipamento em análise, apresentando informações relevantes como a quantidade de eventos similares já registrados, sua distribuição ao longo do tempo, frequência de ocorrência e contexto operacional associado.

Além da análise dos dados históricos, a solução deverá integrar-se à base documental da empresa, permitindo consultar manuais, procedimentos, relatórios técnicos e registros de manutenção relacionados aos eventos identificados. Com base nessas informações, o sistema poderá sugerir possíveis ações de inspeção, manutenção ou correção, auxiliando as equipes técnicas na tomada de decisão.

Dessa forma, a solução proposta não depende necessariamente da classificação prévia de falhas conhecidas, mas sim da identificação de padrões similares dentro do histórico operacional da empresa, combinando análise de dados, busca por similaridade e recuperação de conhecimento para apoiar estratégias de manutenção preditiva e prescritiva.

---

### 2. Cenário do Projeto
A equipe de Automação e Instrumentação da empresa já realizou a instalação de diversos sensores e dispositivos de aquisição de dados. Essas informações são enviadas continuamente para um banco de dados corporativo, previamente modelado e implementado pela equipe de Software da organização.

Com o objetivo de permitir o desenvolvimento paralelo das atividades e acelerar a execução do projeto, os dados foram disponibilizados para a equipe de Inteligência Artificial, responsável pelas análises e desenvolvimento dos modelos prescritivos.

*(Figura 01 - Diagrama Geral das funcionalidades esperadas para a solução)*

**Exemplo de json de entrada:**
```json
{"id":114387,"created_at":"2026-06-01 21:32:53.911176+00:00","z_rms_velocity_in_s":0.0597,"z_rms_velocity_mm_s":1.517,"temperature_f":76.44,"temperature_c":24.69,"x_rms_velocity_in_s":0.0787,"x_rms_velocity_mm_s":2.0,"z_peak_acceleration_g":0.484,"x_peak_acceleration_g":0.631,"z_peak_vel_comp_freq_hz":61.0,"x_peak_vel_comp_freq_hz":61.0,"z_rms_acceleration_g":0.09,"x_rms_acceleration_g":0.114,"z_kurtosis":2.392,"x_kurtosis":2.77,"z_crest_factor":3.747,"x_crest_factor":4.269,"z_peak_velocity_in_s":0.0844,"z_peak_velocity_mm_s":2.146,"x_peak_velocity_in_s":0.1113,"x_peak_velocity_mm_s":2.829,"z_high_freq_rms_accel_g":0.129,"x_high_freq_rms_accel_g":0.147,"fault":"cocked_rotor_2","rpm":1000.0}
```

---

### 3. Desafio Proposto
Desenvolver o pipeline completo de um projeto de Inteligência Artificial, contemplando todas as etapas necessárias para a construção de uma solução de Manutenção Prescritiva.

**O pipeline deve incluir:**
* Arquitetura da Solução;
* Definição de arquitetura técnica para implantação do projeto em ambiente industrial;
* Tratamento dos documentos fornecidos;
* Construção de modelo de linguagem para prestar auxilio quando um novo evento é registrado no sistema, demonstrando como corrigir o problema que aconteceu;
* O sistema deve se deter unicamente a problemas que possuem documentos, caso contrário deve reportar que ainda não existe o problema identificado e sugerir ao usuário para registrar um novo documento para o defeito;
* Apresentação visual dos resultados através de dashboards, gráficos, relatórios ou aplicações interativas.

---

### 4. Liberdade de Implementação
O candidato possui liberdade para:
* Escolher a estratégia de resolução;
* Escolher as ferramentas complementares utilizadas no projeto.

---

### 5. Restrições
Alguma restrições devem ser respeitadas para o desenvolvimento do projeto:
* Deve ser utilizado linguagem de programação Python.
* O treinamento dos modelos poderá ser realizado em infraestrutura computacional de alto desempenho, sem restrições específicas de processamento. Entretanto, a solução final disponibilizada para operação, deverá ser capaz de executar inferências, consultas e recomendações em uma estação de trabalho comercial equipada com até 32 GB de memória RAM e uma GPU com 16 GB de memória dedicada.

---

### 6. Descrição dos dados
Existe um arquivo chamado "banner.csv". Este arquivo contém uma coluna de identificação do registro ("id"), data de criação ("created_at"), Condição anotada manualmente pelo operador ("fault"), e dados de métricas estatísticas extraídas de sensores de vibração instalados diferentes pontos de uma máquina rotativa (colunas restantes).

Na coluna "fault", os itens "normal", "baseline", "teste", "acelerando" e "motor_desligado" não representam problemas, mas sim estados do sistema. Os demais rótulos devem ser identificados como problemas.

Além dos dados, também são fornecidos os arquivos que a empresa tem sobre a documentação das falhas.

---

### 7. Link para Download dos Dados
https://drive.google.com/drive/folders/18iEQsPWE8d0S-gDt56sGgnN8QtYshQPB?usp=drive_link

---

### CRITÉRIOS DE AVALIAÇÃO
A avaliação será composta por duas etapas:
1. Entrega do Projeto;
2. Entrevista de Apresentação do Projeto.

**Avaliação da Entrega do Projeto**
Serão considerados os seguintes critérios:
* Arquitetura e Planejamento
  * Arquitetura proposta para implantação do projeto;
* Desenvolvimento da Solução
  * Organização do código;
  * Qualidade da implementação;
  * Organização do repositório GitHub;
  * Versionamento;
  * Documentação;
  * Interpretação do problema;
  * Entendimento dos objetivos do projeto.

**Avaliação da Entrevista**
Durante a entrevista serão avaliados:
* Apresentação do Projeto
  * Clareza na comunicação;
  * Organização da apresentação;
  * Justificativa das decisões técnicas adotadas;
  * Capacidade de argumentação;
  * Domínio dos conceitos utilizados;
  * Justificativa dos resultados obtidos;
  * Interpretação dos resultados;
  * Demonstração com dados de teste;
  * Capacidade de extrair insights relevantes;
  * Alucinação do modelo.

---

### OBSERVAÇÕES
* **OBS 1:** O candidato deve realizar a submissão do projeto mesmo que alguma das etapas previstas não tenha sido concluída integralmente.
* **OBS 2:** A apresentação pode ser realizada utilizando qualquer ferramenta, incluindo:
  * PowerPoint;
  * Jupyter Notebook;
  * Google Colab;
  * Streamlit;
  * Dash;
  * Outras ferramentas equivalentes.
* **OBS 3:** Espera-se uma interação mínima com o modelo/chat durante a apresentação da solução.

---

### DIFERENCIAL
Será considerado um diferencial a implementação de:
* APIs;
* Bancos de Dados;
* Dashboards;
* Soluções de Deploy;
* Integrações em ambiente industrial.

**Boa Prova!**

---
*Código do Formulário: FM-014-NP-0801 | Revisão 01 | Data da Revisão: 01/07/2026 | Páginas 1 a 4*