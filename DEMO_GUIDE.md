# 📚 Guia de Demonstração: Filtragem Colaborativa

## Como Funciona Cada Algoritmo

### 1. User-Based Collaborative Filtering (CF Baseado em Usuário)

**Conceito**: "Usuários similares gostam de coisas similares"

**Funcionamento**:
1. Calcula a similaridade entre usuários usando cosseno nas avaliações
2. Para recomendar ao Usuário A:
   - Encontra os K usuários mais similares (vizinhos)
   - Vê quais itens os vizinhos avaliaram bem
   - Recomenda itens que o Usuário A ainda não viu

**Exemplo Prático**:
```
Usuário 1: Like em X(5), Like em Y(5)
Usuário 2: Like em X(5), Like em Z(5)

Similaridade entre Usuário 1 e 2:
- Ambos avaliaram X com nota 5 → Alta similaridade

Recomendações:
- Para Usuário 1: Item Z (porque usuário similar 2 gostou)
- Para Usuário 2: Item Y (porque usuário similar 1 gostou)
```

**Como Demonstrar no Sistema**:
1. Usuário 1001: Dê like em 2-3 itens específicos
2. Usuário 1002: Dê like em 1-2 dos mesmos itens + 1 item diferente
3. Regenere as recomendações: `python recsys/generate_recommendations.py --models user_based_cf --top-n 50`
4. Verifique que cada usuário recebe recomendações dos itens que o outro gostou

---

### 2. Item-Based Collaborative Filtering (CF Baseado em Item)

**Conceito**: "Itens similares são avaliados de forma similar pelos mesmos usuários"

**Funcionamento**:
1. Calcula similaridade entre itens baseado em quem os avaliou
2. Para recomendar ao Usuário A:
   - Vê quais itens o usuário já avaliou positivamente
   - Encontra itens similares a esses
   - Recomenda os itens mais similares que o usuário não viu

**Exemplo Prático**:
```
Item X foi avaliado por: Usuário 1(5), Usuário 2(5), Usuário 3(4)
Item Y foi avaliado por: Usuário 1(5), Usuário 2(4), Usuário 4(5)

Similaridade entre X e Y:
- Usuários 1 e 2 avaliaram ambos positivamente → Alta similaridade

Se Usuário 5 der like em X:
→ Sistema recomenda Y (item similar a X)
```

**Como Demonstrar no Sistema**:
1. Identifique 2-3 itens que têm avaliações de usuários em comum (consulte o banco)
2. Como Usuário 1001: Dê like em um desses itens
3. Regenere: `python recsys/generate_recommendations.py --models item_based_cf --top-n 50`
4. Verifique que recebe recomendações dos itens similares

---

### 3. Matrix Factorization (SVD)

**Conceito**: "Decomposição em fatores latentes (características ocultas)"

**Funcionamento**:
1. Decompõe a matriz usuário-item (70x546) em duas matrizes menores:
   - Matriz de usuários × fatores latentes
   - Matriz de fatores latentes × itens
2. Fatores latentes capturam características não explícitas (ex: "tecnologia", "entretenimento")
3. Prediz avaliações multiplicando as matrizes
4. Recomenda itens com maior predição

**Exemplo Prático**:
```
Sistema descobre 50 fatores latentes (N_COMPONENTS=50)

Fator 1: "Tecnologia" - usuários que gostam de apps tech
Fator 2: "Entretenimento" - usuários que gostam de jogos/mídia
...

Usuário 1:
- Alto score no Fator 1 (0.8)
- Baixo score no Fator 2 (0.2)
→ Recebe recomendações de itens com alto score no Fator 1

Item X:
- Alto score no Fator 1 (0.9)
- Médio score no Fator 2 (0.5)
→ Recomendado para usuários com perfil "tech"
```

**Como Demonstrar no Sistema**:
1. Dê likes em itens de uma categoria específica (ex: todos de "tecnologia")
2. Dê dislikes em itens de outra categoria (ex: "entretenimento")
3. Regenere: `python recsys/generate_recommendations.py --models matrix_factorization --top-n 50`
4. Observe que as recomendações seguem o padrão de preferências latentes

---

## Integração Like/Dislike = Ratings

**Mapeamento**:
- `Like` → Rating 5.0 (nota máxima)
- `Dislike` → Rating 1.0 (nota mínima)
- Feedback SOBRESCREVE ratings originais da mesma combinação (user_id, item_id)

**Fluxo**:
1. Sistema carrega ratings da tabela `ratings`
2. Sistema carrega feedback da tabela `user_feedback`
3. Se um usuário deu like/dislike em um item que já tinha rating, o feedback prevalece
4. Todos são normalizados para [0, 1] antes do treinamento

**Código Relevante** (`collaborative_filtering.py`):
```python
FEEDBACK_LIKE_RATING = 5.0
FEEDBACK_DISLIKE_RATING = 1.0

def _load_ratings_from_sqlite(db_path):
    # 1. Carrega ratings originais
    ratings_by_pair = {...}  # (user_id, item_id) → rating

    # 2. Sobrescreve com feedback
    for user_id, item_id, feedback_type in user_feedback:
        if feedback_type == "like":
            ratings_by_pair[(user_id, item_id)] = 5.0
        elif feedback_type == "dislike":
            ratings_by_pair[(user_id, item_id)] = 1.0
```

---

## Roteiro de Demonstração Completa

### Setup Inicial
```bash
# 1. Certifique-se que o banco está atualizado
cd /Users/gustavoroos/projects/personal/mestrado/rec
python data/create_db.py

# 2. Limpe feedbacks anteriores (opcional)
# No frontend, clique em "Resetar Feedbacks"
```

### Demonstração User-Based CF

**Cenário**: Demonstrar que usuários similares recebem recomendações similares

```bash
# 1. No sistema web:
# - Logue como Usuário 1001
# - Dê LIKE em itens: 10, 15, 20
# - Dê DISLIKE em item: 5

# 2. Troque para Usuário 1002
# - Dê LIKE em itens: 10, 15, 25
# - Dê DISLIKE em item: 8

# 3. Regenere recomendações
python recsys/generate_recommendations.py --models user_based_cf --top-n 50

# 4. Volte ao sistema web
# - Usuário 1001 deve receber item 25 (que 1002 gostou)
# - Usuário 1002 deve receber item 20 (que 1001 gostou)
# - Itens 5 e 8 não aparecem para ninguém
```

### Demonstração Item-Based CF

**Cenário**: Demonstrar itens similares sendo recomendados

```bash
# 1. Identifique itens similares (consulta no banco)
sqlite3 data/data.db "
  SELECT i1.item_id as item1, i2.item_id as item2, COUNT(*) as common_users
  FROM ratings i1
  JOIN ratings i2 ON i1.user_id = i2.user_id AND i1.item_id < i2.item_id
  WHERE i1.rating >= 4 AND i2.rating >= 4
  GROUP BY i1.item_id, i2.item_id
  HAVING common_users >= 3
  ORDER BY common_users DESC
  LIMIT 5
"

# 2. Exemplo: Itens 31 e 35 são similares
# - Usuário 1001: Dê LIKE em item 31
# - Regenere: python recsys/generate_recommendations.py --models item_based_cf --top-n 50
# - Verifique que item 35 aparece nas recomendações

# 3. Usuário 1002: Dê LIKE em item 35
# - Verifique que item 31 aparece nas recomendações
```

### Demonstração Matrix Factorization

**Cenário**: Demonstrar aprendizado de preferências latentes por categoria

```bash
# 1. Consulte itens por categoria
sqlite3 data/data.db "
  SELECT c.name, GROUP_CONCAT(ic.item_id) as items
  FROM categories c
  JOIN item_categories ic ON c.id = ic.category_id
  GROUP BY c.id
  LIMIT 10
"

# 2. Escolha uma categoria (ex: "technology")
# - Usuário 1001: Dê LIKE em TODOS os itens dessa categoria
# - Usuário 1001: Dê DISLIKE em itens de outra categoria

# 3. Regenere
python recsys/generate_recommendations.py --models matrix_factorization --top-n 50

# 4. Observe que as recomendações são predominantemente da categoria preferida
# Isso acontece porque o SVD identificou o fator latente "technology" para o usuário
```

---

## Queries Úteis para Demonstração

### Ver ratings atuais + feedback de um usuário
```sql
SELECT
    user_id,
    item_id,
    rating as original_rating,
    (SELECT feedback_type FROM user_feedback
     WHERE user_id = r.user_id AND item_id = r.item_id) as feedback
FROM ratings r
WHERE user_id = 1001
ORDER BY item_id;
```

### Ver quais usuários são similares (avaliaram os mesmos itens)
```sql
SELECT
    r1.user_id as user1,
    r2.user_id as user2,
    COUNT(*) as common_items,
    AVG(ABS(r1.rating - r2.rating)) as avg_diff
FROM ratings r1
JOIN ratings r2 ON r1.item_id = r2.item_id AND r1.user_id < r2.user_id
GROUP BY r1.user_id, r2.user_id
HAVING common_items >= 5
ORDER BY common_items DESC, avg_diff ASC
LIMIT 10;
```

### Ver itens similares (avaliados pelos mesmos usuários)
```sql
SELECT
    r1.item_id as item1,
    r2.item_id as item2,
    COUNT(*) as common_users,
    AVG(ABS(r1.rating - r2.rating)) as avg_diff
FROM ratings r1
JOIN ratings r2 ON r1.user_id = r2.user_id AND r1.item_id < r2.item_id
WHERE r1.rating >= 4 AND r2.rating >= 4
GROUP BY r1.item_id, r2.item_id
HAVING common_users >= 3
ORDER BY common_users DESC
LIMIT 10;
```

### Ver estatísticas de feedback
```sql
SELECT
    feedback_type,
    COUNT(*) as count,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT item_id) as unique_items
FROM user_feedback
GROUP BY feedback_type;
```

---

## Parâmetros Configuráveis

Em `collaborative_filtering.py`:

```python
MIN_COMMON_RATINGS = 2      # Mínimo de ratings em comum para calcular similaridade
K_NEIGHBORS = 20            # Número de vizinhos mais similares a considerar
N_COMPONENTS = 50           # Dimensões latentes no SVD
FEEDBACK_LIKE_RATING = 5.0  # Mapeamento de like
FEEDBACK_DISLIKE_RATING = 1.0  # Mapeamento de dislike
```

Ajuste esses valores para experimentar diferentes comportamentos!
