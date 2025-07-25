# Contratos de API - Site Consórcio Volkswagen

## Visão Geral
Este documento define os contratos entre frontend e backend para o site de captação de leads do consórcio Volkswagen.

## Dados Mockados (Frontend Atual)
- **Carros VW**: 4 modelos (Golf GTI, Polo Track, T-Cross, Nivus) com imagens, preços e características
- **Depoimentos**: 3 depoimentos de clientes contemplados
- **Posts do Blog**: 3 artigos educativos sobre consórcio
- **Formulários**: Captação de leads com nome, WhatsApp, cidade e modelo desejado

## Estruturas de Dados

### Lead (Formulário Principal)
```javascript
{
  id: String (UUID),
  name: String (required),
  whatsapp: String (required),
  city: String (required),
  model: String (required), // Nome do carro desejado
  source: String, // "hero-form", "car-interest", etc.
  createdAt: Date,
  status: String // "new", "contacted", "converted"
}
```

### Car
```javascript
{
  id: String,
  name: String, // "Golf GTI 2025"
  model: String, // "Golf GTI"
  year: Number,
  image: String (URL),
  monthlyPrice: String, // "R$ 1.247"
  totalCredit: String, // "R$ 89.000"
  installments: Number,
  highlights: Array[String],
  description: String,
  isActive: Boolean
}
```

### Testimonial
```javascript
{
  id: String,
  name: String,
  city: String,
  car: String,
  image: String (URL),
  testimonial: String,
  rating: Number (1-5),
  contemplated: Boolean,
  monthsToContemplate: Number,
  isActive: Boolean
}
```

### BlogPost
```javascript
{
  id: String,
  title: String,
  excerpt: String,
  slug: String,
  category: String,
  readTime: String,
  publishedAt: Date,
  content: String,
  isPublished: Boolean
}
```

## Endpoints Necessários

### 1. Leads
- **POST /api/leads** - Criar novo lead
  - Body: { name, whatsapp, city, model, source }
  - Response: Lead criado com ID

- **GET /api/leads** - Listar leads (admin)
- **PUT /api/leads/:id** - Atualizar status do lead
- **GET /api/leads/stats** - Estatísticas de leads

### 2. Carros
- **GET /api/cars** - Listar carros ativos
- **POST /api/cars** - Criar carro (admin)
- **PUT /api/cars/:id** - Atualizar carro (admin)
- **DELETE /api/cars/:id** - Remover carro (admin)

### 3. Depoimentos
- **GET /api/testimonials** - Listar depoimentos ativos
- **POST /api/testimonials** - Criar depoimento (admin)
- **PUT /api/testimonials/:id** - Atualizar depoimento (admin)

### 4. Blog
- **GET /api/blog/posts** - Listar posts publicados
- **GET /api/blog/posts/:slug** - Obter post por slug
- **POST /api/blog/posts** - Criar post (admin)
- **PUT /api/blog/posts/:id** - Atualizar post (admin)

### 5. Analytics
- **POST /api/analytics/page-view** - Registrar visualização
- **POST /api/analytics/form-interaction** - Registrar interação com formulário
- **GET /api/analytics/dashboard** - Dashboard de métricas (admin)

## Integração Frontend → Backend

### 1. Hero Section (HeroSection.jsx)
- **Remover**: Mock data de mockCars
- **Adicionar**: useEffect para buscar carros da API
- **Integrar**: handleSubmit para POST /api/leads

### 2. Featured Cars (FeaturedCars.jsx)  
- **Remover**: Import do mockCars
- **Adicionar**: useEffect para GET /api/cars
- **Integrar**: handleCarInterest para POST /api/leads com source "car-interest"

### 3. Testimonials (Testimonials.jsx)
- **Remover**: Import do mockTestimonials  
- **Adicionar**: useEffect para GET /api/testimonials

### 4. Blog Section (BlogSection.jsx)
- **Remover**: Import do mockBlogPosts
- **Adicionar**: useEffect para GET /api/blog/posts
- **Integrar**: Links reais para posts individuais

### 5. Analytics
- **Adicionar**: Tracking de page views e interações
- **Implementar**: useEffect em componentes principais para analytics

## Funcionalidades Especiais

### 1. WhatsApp Integration
- URLs já configuradas com o número: 5591992379276
- Mensagens personalizadas por contexto (lead form, interesse em carro específico, etc.)

### 2. Form Validations
- Validação de WhatsApp brasileiro
- Validação de nome completo
- Validação de cidade
- Modelo obrigatório

### 3. Lead Sources
- "hero-form": Formulário principal
- "car-interest": Interesse em carro específico
- "blog-interest": Interesse via blog
- "whatsapp-direct": Clique direto no WhatsApp

### 4. SEO & Performance
- Meta tags dinâmicas para blog posts
- Lazy loading de imagens
- Otimização de Core Web Vitals

## Próximos Passos

1. **Implementar backend** com MongoDB
2. **Criar endpoints** conforme especificado
3. **Integrar frontend** removendo mocks
4. **Implementar analytics** básico
5. **Testes de funcionamento** end-to-end

## Observações Técnicas

- Usar axios para requests HTTP
- Implementar error handling apropriado
- Loading states para melhor UX
- Toast notifications para feedback
- Validação tanto no frontend quanto backend