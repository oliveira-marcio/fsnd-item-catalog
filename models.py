# TODO: Criar banco de dados
"""
Users:
- id (Integer, primary_key=True)
- name (String(250), nullable=False)
- email (String(250), nullable=False)
- picture (String(250))

Categories:
- id (Integer, primary_key=True)
- name (String(100), nullable=False)

Items:
- id (Integer, primary_key=True)
- title (String(100), nullable=False)
- description (String(2000), nullable=False)
- cat_id (Integer, ForeignKey('categories.id'))
- user_id (Integer, ForeignKey('users.id'))
"""

# TODO: Serializar categorias e itens
