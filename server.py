from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Volkswagen Consortium API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models for Volkswagen Consortium
class LeadCreate(BaseModel):
    name: str
    whatsapp: str
    city: str
    model: str
    source: str = "hero-form"

class Lead(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    whatsapp: str
    city: str
    model: str
    source: str = "hero-form"
    status: str = "new"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Car(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    model: str
    year: int
    image: str
    monthly_price: str
    total_credit: str
    installments: int
    highlights: List[str]
    description: str
    is_active: bool = True

class Testimonial(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    city: str
    car: str
    image: str
    testimonial: str
    rating: int
    contemplated: bool
    months_to_contemplate: int
    is_active: bool = True

class BlogPost(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    excerpt: str
    slug: str
    category: str
    read_time: str
    published_at: datetime
    content: str = ""
    is_published: bool = True

# Legacy models for compatibility
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Volkswagen Consortium API - Running!", "version": "1.0.0"}

# Legacy status endpoints
@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Leads endpoints
@api_router.post("/leads", response_model=Lead)
async def create_lead(lead_data: LeadCreate):
    """Create a new lead from form submission"""
    lead_dict = lead_data.dict()
    lead_obj = Lead(**lead_dict)
    result = await db.leads.insert_one(lead_obj.dict())
    if result.inserted_id:
        return lead_obj
    raise HTTPException(status_code=400, detail="Failed to create lead")

@api_router.get("/leads", response_model=List[Lead])
async def get_leads():
    """Get all leads (admin endpoint)"""
    leads = await db.leads.find().sort("created_at", -1).to_list(1000)
    return [Lead(**lead) for lead in leads]

@api_router.get("/leads/stats")
async def get_lead_stats():
    """Get lead statistics"""
    total_leads = await db.leads.count_documents({})
    new_leads = await db.leads.count_documents({"status": "new"})
    contacted_leads = await db.leads.count_documents({"status": "contacted"})
    converted_leads = await db.leads.count_documents({"status": "converted"})
    
    # Group by source
    pipeline = [
        {"$group": {"_id": "$source", "count": {"$sum": 1}}}
    ]
    sources = await db.leads.aggregate(pipeline).to_list(100)
    
    return {
        "total": total_leads,
        "new": new_leads,
        "contacted": contacted_leads,
        "converted": converted_leads,
        "by_source": {source["_id"]: source["count"] for source in sources}
    }

@api_router.put("/leads/{lead_id}")
async def update_lead_status(lead_id: str, status: str):
    """Update lead status"""
    result = await db.leads.update_one(
        {"id": lead_id},
        {"$set": {"status": status}}
    )
    if result.modified_count:
        return {"message": "Lead updated successfully"}
    raise HTTPException(status_code=404, detail="Lead not found")

# Cars endpoints
@api_router.get("/cars", response_model=List[Car])
async def get_cars():
    """Get all active cars"""
    cars = await db.cars.find({"is_active": True}).to_list(100)
    return [Car(**car) for car in cars]

@api_router.post("/cars", response_model=Car)
async def create_car(car_data: Car):
    """Create a new car (admin)"""
    result = await db.cars.insert_one(car_data.dict())
    if result.inserted_id:
        return car_data
    raise HTTPException(status_code=400, detail="Failed to create car")

@api_router.put("/cars/{car_id}")
async def update_car(car_id: str, car_data: Car):
    """Update car information"""
    result = await db.cars.update_one(
        {"id": car_id},
        {"$set": car_data.dict()}
    )
    if result.modified_count:
        return {"message": "Car updated successfully"}
    raise HTTPException(status_code=404, detail="Car not found")

@api_router.delete("/cars/{car_id}")
async def delete_car(car_id: str):
    """Soft delete car (set is_active to False)"""
    result = await db.cars.update_one(
        {"id": car_id},
        {"$set": {"is_active": False}}
    )
    if result.modified_count:
        return {"message": "Car deleted successfully"}
    raise HTTPException(status_code=404, detail="Car not found")

# Testimonials endpoints
@api_router.get("/testimonials", response_model=List[Testimonial])
async def get_testimonials():
    """Get all active testimonials"""
    testimonials = await db.testimonials.find({"is_active": True}).to_list(100)
    return [Testimonial(**testimonial) for testimonial in testimonials]

@api_router.post("/testimonials", response_model=Testimonial)
async def create_testimonial(testimonial_data: Testimonial):
    """Create a new testimonial (admin)"""
    result = await db.testimonials.insert_one(testimonial_data.dict())
    if result.inserted_id:
        return testimonial_data
    raise HTTPException(status_code=400, detail="Failed to create testimonial")

@api_router.put("/testimonials/{testimonial_id}")
async def update_testimonial(testimonial_id: str, testimonial_data: Testimonial):
    """Update testimonial"""
    result = await db.testimonials.update_one(
        {"id": testimonial_id},
        {"$set": testimonial_data.dict()}
    )
    if result.modified_count:
        return {"message": "Testimonial updated successfully"}
    raise HTTPException(status_code=404, detail="Testimonial not found")

# Blog endpoints
@api_router.get("/blog/posts", response_model=List[BlogPost])
async def get_blog_posts():
    """Get all published blog posts"""
    posts = await db.blog_posts.find({"is_published": True}).sort("published_at", -1).to_list(100)
    return [BlogPost(**post) for post in posts]

@api_router.get("/blog/posts/{slug}")
async def get_blog_post_by_slug(slug: str):
    """Get a specific blog post by slug"""
    post = await db.blog_posts.find_one({"slug": slug, "is_published": True})
    if post:
        return BlogPost(**post)
    raise HTTPException(status_code=404, detail="Post not found")

@api_router.post("/blog/posts", response_model=BlogPost)
async def create_blog_post(post_data: BlogPost):
    """Create a new blog post (admin)"""
    result = await db.blog_posts.insert_one(post_data.dict())
    if result.inserted_id:
        return post_data
    raise HTTPException(status_code=400, detail="Failed to create blog post")

@api_router.put("/blog/posts/{post_id}")
async def update_blog_post(post_id: str, post_data: BlogPost):
    """Update blog post"""
    result = await db.blog_posts.update_one(
        {"id": post_id},
        {"$set": post_data.dict()}
    )
    if result.modified_count:
        return {"message": "Blog post updated successfully"}
    raise HTTPException(status_code=404, detail="Blog post not found")

# Analytics endpoints (basic implementation)
@api_router.post("/analytics/page-view")
async def log_page_view(page: str, user_agent: str = "", ip: str = ""):
    """Log a page view for analytics"""
    view_data = {
        "id": str(uuid.uuid4()),
        "page": page,
        "user_agent": user_agent,
        "ip": ip,
        "timestamp": datetime.utcnow()
    }
    await db.page_views.insert_one(view_data)
    return {"message": "Page view logged"}

@api_router.post("/analytics/form-interaction")
async def log_form_interaction(form_type: str, action: str, details: dict = {}):
    """Log form interactions"""
    interaction_data = {
        "id": str(uuid.uuid4()),
        "form_type": form_type,
        "action": action,
        "details": details,
        "timestamp": datetime.utcnow()
    }
    await db.form_interactions.insert_one(interaction_data)
    return {"message": "Form interaction logged"}

@api_router.get("/analytics/dashboard")
async def get_analytics_dashboard():
    """Get basic analytics dashboard data"""
    total_leads = await db.leads.count_documents({})
    total_page_views = await db.page_views.count_documents({})
    total_form_interactions = await db.form_interactions.count_documents({})
    
    # Most popular cars (based on leads)
    pipeline = [
        {"$group": {"_id": "$model", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    popular_cars = await db.leads.aggregate(pipeline).to_list(5)
    
    return {
        "total_leads": total_leads,
        "total_page_views": total_page_views,
        "total_form_interactions": total_form_interactions,
        "popular_cars": popular_cars
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize database with sample data if empty"""
    logger.info("Starting up Volkswagen Consortium API...")
    
    # Check if we need to populate initial data
    cars_count = await db.cars.count_documents({})
    if cars_count == 0:
        await populate_initial_data()

async def populate_initial_data():
    """Populate database with initial sample data"""
    logger.info("Populating initial data...")
    
    # Initial cars data based on mock.js
    initial_cars = [
        {
            "id": "golf-gti-2025",
            "name": "Golf GTI 2025",
            "model": "Golf GTI",
            "year": 2025,
            "image": "https://images.unsplash.com/photo-1574581501439-6405a98bd76c?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDN8MHwxfHNlYXJjaHwxfHx2b2xrc3dhZ2VuJTIwZ29sZnxlbnwwfHx8fDE3NTMwMTkxODh8MA&ixlib=rb-4.1.0&q=85",
            "monthly_price": "R$ 1.247",
            "total_credit": "R$ 89.000",
            "installments": 60,
            "highlights": ["Motor 2.0 TSI", "250cv de potência", "Tração dianteira"],
            "description": "O Golf GTI é a versão esportiva mais desejada do segmento premium.",
            "is_active": True
        },
        {
            "id": "polo-track-2025",
            "name": "Polo Track",
            "model": "Polo Track",
            "year": 2025,
            "image": "https://images.unsplash.com/photo-1630485074308-ff80bde93658?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHwxfHx2b2xrc3dhZ2VuJTIwcG9sb3xlbnwwfHx8fDE3NTMwMTkxOTV8MA&ixlib=rb-4.1.0&q=85",
            "monthly_price": "R$ 847",
            "total_credit": "R$ 65.000",
            "installments": 60,
            "highlights": ["Motor 1.0 TSI", "Design arrojado", "Tecnologia avançada"],
            "description": "O Polo Track combina esportividade e economia para o dia a dia.",
            "is_active": True
        },
        {
            "id": "t-cross-2025",
            "name": "T-Cross",
            "model": "T-Cross",
            "year": 2025,
            "image": "https://images.unsplash.com/photo-1692377789658-e37e26cc2db7?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHwyfHx2b2xrc3dhZ2VuJTIwc3V2fGVufDB8fHx8MTc1MzAxOTIwMnww&ixlib=rb-4.1.0&q=85",
            "monthly_price": "R$ 987",
            "total_credit": "R$ 78.000",
            "installments": 60,
            "highlights": ["SUV compacto", "Espaço interno", "Posição elevada"],
            "description": "O T-Cross é o SUV perfeito para quem busca versatilidade e conforto.",
            "is_active": True
        },
        {
            "id": "nivus-2025",
            "name": "Nivus",
            "model": "Nivus",
            "year": 2025,
            "image": "https://images.unsplash.com/photo-1705229810194-dd78431dcb78?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHwzfHx2b2xrc3dhZ2VuJTIwc3V2fGVufDB8fHx8MTc1MzAxOTIwMnww&ixlib=rb-4.1.0&q=85",
            "monthly_price": "R$ 897",
            "total_credit": "R$ 72.000",
            "installments": 60,
            "highlights": ["SUV Coupé", "Design único", "Eficiência energética"],
            "description": "O Nivus representa a nova era dos SUVs coupé da Volkswagen.",
            "is_active": True
        }
    ]
    
    # Initial testimonials
    initial_testimonials = [
        {
            "id": "testimonial-1",
            "name": "Maria Silva",
            "city": "Belém, PA",
            "car": "T-Cross 2024",
            "image": "https://images.unsplash.com/photo-1494790108755-2616c6d58a37?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDN8MHwxfHNlYXJjaHwyNHx8cGVyc29uJTIwcG9ydHJhaXR8ZW58MHx8fHwxNzUzMDE5MjA2fDA&ixlib=rb-4.1.0&q=85",
            "testimonial": "Achei que era impossível ter meu carro sem entrada... hoje tenho meu T-Cross sem pagar juros! O Ismael me ajudou em todo o processo.",
            "rating": 5,
            "contemplated": True,
            "months_to_contemplate": 8,
            "is_active": True
        },
        {
            "id": "testimonial-2",
            "name": "João Santos",
            "city": "Ananindeua, PA",
            "car": "Golf GTI 2024",
            "image": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDN8MHwxfHNlYXJjaHwxN3x8cGVyc29uJTIwcG9ydHJhaXR8ZW58MHx8fHwxNzUzMDE5MjA2fDA&ixlib=rb-4.1.0&q=85",
            "testimonial": "Sempre sonhei com um Golf GTI. Com o consórcio consegui realizar esse sonho sem comprometer minha renda. Recomendo!",
            "rating": 5,
            "contemplated": True,
            "months_to_contemplate": 12,
            "is_active": True
        },
        {
            "id": "testimonial-3",
            "name": "Ana Oliveira",
            "city": "Castanhal, PA",
            "car": "Polo Track 2024",
            "image": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDN8MHwxfHNlYXJjaHwyNnx8cGVyc29uJTIwcG9ydHJhaXR8ZW58MHx8fHwxNzUzMDE5MjA2fDA&ixlib=rb-4.1.0&q=85",
            "testimonial": "Excelente atendimento! Consegui meu Polo Track em apenas 6 meses. O processo foi super transparente e sem pegadinhas.",
            "rating": 5,
            "contemplated": True,
            "months_to_contemplate": 6,
            "is_active": True
        }
    ]
    
    # Initial blog posts
    initial_blog_posts = [
        {
            "id": "blog-1",
            "title": "5 motivos para escolher consórcio em vez de financiamento",
            "excerpt": "Descubra por que o consórcio é uma opção mais inteligente que o financiamento tradicional...",
            "slug": "consorcio-vs-financiamento",
            "category": "Educativo",
            "read_time": "5 min",
            "published_at": datetime(2025, 1, 15),
            "content": "Conteúdo completo do artigo sobre consórcio vs financiamento...",
            "is_published": True
        },
        {
            "id": "blog-2",
            "title": "Como ser contemplado mais rápido no consórcio",
            "excerpt": "Estratégias comprovadas para aumentar suas chances de contemplação antecipada...",
            "slug": "contemplacao-rapida-consorcio",
            "category": "Dicas",
            "read_time": "7 min",
            "published_at": datetime(2025, 1, 12),
            "content": "Conteúdo completo sobre contemplação rápida...",
            "is_published": True
        },
        {
            "id": "blog-3",
            "title": "Diferença entre carta de crédito e financiamento",
            "excerpt": "Entenda as principais diferenças e qual opção é melhor para seu perfil...",
            "slug": "carta-credito-vs-financiamento",
            "category": "Comparativo",
            "read_time": "4 min",
            "published_at": datetime(2025, 1, 10),
            "content": "Conteúdo completo sobre carta de crédito vs financiamento...",
            "is_published": True
        }
    ]
    
    # Insert initial data
    await db.cars.insert_many(initial_cars)
    await db.testimonials.insert_many(initial_testimonials)
    await db.blog_posts.insert_many(initial_blog_posts)
    
    logger.info("Initial data populated successfully!")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
