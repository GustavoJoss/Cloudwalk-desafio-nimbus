# app/seed_dataset.py

"""
Dataset embutido com informações essenciais da CloudWalk.
Esses textos vão entrar no índice vetorial e no BM25
junto com o restante das páginas raspadas.
"""

SEED_DOCS = [
    {
        "url": "https://www.cloudwalk.io/#our-mission",
        "text": (
            "Missão da CloudWalk\n\n"
            "A missão da CloudWalk é criar a melhor rede de pagamentos do planeta – "
            "e depois de outros planetas – democratizando a indústria financeira e "
            "empoderando empreendedores por meio de soluções tecnológicas inclusivas "
            "e transformadoras. A empresa busca substituir estruturas tradicionais de "
            "pagamento, muitas vezes concentradas e caras, por um modelo mais justo, "
            "eficiente e acessível para pequenos e médios negócios."
        ),
    },
    {
        "url": "https://www.cloudwalk.io/#our-pillars",
        "text": (
            "Pilares e valores da CloudWalk\n\n"
            "Best Product: foco em construir o melhor produto possível em termos de "
            "tecnologia, performance e experiência. Isso envolve uso intensivo de "
            "inteligência artificial, automação e infraestruturas modernas para entregar "
            "pagamentos rápidos, confiáveis e com excelente usabilidade para lojistas.\n\n"
            "Customer Engagement: os clientes ficam no centro das decisões. A CloudWalk "
            "trata os empreendedores como parceiros de longo prazo, ouvindo feedback, "
            "co-criando soluções e permitindo que eles influenciem diretamente o produto "
            "e o rumo do negócio. A relação é contínua, transparente e baseada em confiança.\n\n"
            "Disruptive Economics: compromisso com um modelo econômico que beneficia o "
            "lojista, reduzindo custos de aceitação, liberando poder de compra e melhorando "
            "a margem dos negócios. A ideia é quebrar estruturas de preços tradicionais, "
            "criando uma economia de pagamentos mais eficiente e acessível."
        ),
    },
    {
        "url": "https://www.cloudwalk.io/#facts",
        "text": (
            "Fatos essenciais e visão da CloudWalk\n\n"
            "A CloudWalk é uma empresa brasileira de tecnologia financeira sediada em São Paulo. "
            "Ela nasceu com o objetivo de transformar a indústria de pagamentos, reduzindo custos "
            "para empreendedores e substituindo modelos tradicionais por soluções mais justas e "
            "eficientes.\n\n"
            "Fundação e fundador: a companhia foi fundada por Luis Silva, que atua como CEO. Desde "
            "o início, a proposta é usar tecnologia de ponta, como inteligência artificial e "
            "infraestrutura própria, para competir com adquirentes tradicionais e novas fintechs.\n\n"
            "Visão de futuro: a missão de 'criar a melhor rede de pagamentos na Terra e em outros "
            "planetas' resume a ambição de longo prazo da empresa: construir uma infraestrutura de "
            "pagamentos global, escalável e acessível, que democratize o acesso a serviços "
            "financeiros.\n\n"
            "Relação com InfinitePay: a InfinitePay é a marca de soluções de pagamento da CloudWalk "
            "voltada para pequenos e médios empreendedores. Quando um lojista usa maquininha ou "
            "links da InfinitePay, ele está utilizando a tecnologia e a infraestrutura desenvolvidas "
            "pela CloudWalk."
        ),
    },
    {
        "url": "https://www.cloudwalk.io/code-of-ethics-and-conduct",
        "text": (
            "Código de Ética e Conduta da CloudWalk\n\n"
            "O Código de Ética e Conduta da CloudWalk orienta o comportamento esperado de "
            "colaboradores, parceiros, fornecedores e prestadores de serviço. Ele reforça o "
            "compromisso da empresa com integridade, transparência e conformidade com leis e "
            "regulamentos.\n\n"
            "Conflitos de interesse: colaboradores devem evitar situações em que interesses "
            "pessoais possam interferir em decisões tomadas em nome da empresa. Negócios privados "
            "com clientes, fornecedores ou parceiros exigem avaliação prévia de compliance e da "
            "liderança.\n\n"
            "Uso da marca e comunicação externa: quem representa a CloudWalk em eventos, "
            "entrevistas, podcasts ou painéis deve alinhar previamente com sua liderança e com o "
            "time responsável pela marca. O uso do logotipo, identidade visual e demais ativos de "
            "marca deve seguir os padrões definidos pela empresa.\n\n"
            "Prevenção a ilícitos: a CloudWalk não tolera envolvimento, mesmo involuntário, em "
            "atividades ilegais, como lavagem de dinheiro ou financiamento ao terrorismo. Há "
            "processos de compliance e canais de reporte para qualquer suspeita de irregularidade.\n\n"
            "Ambiente de trabalho: o Código também reforça o compromisso com um ambiente de trabalho "
            "respeitoso, diverso e livre de assédio ou discriminação, alinhado aos valores e à "
            "cultura da empresa."
        ),
    },
]
