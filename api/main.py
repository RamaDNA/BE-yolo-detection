from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

#from routers import detection_router
from routers import line_detect_realtime_ws_v2
# from routers.rest_state_router import router as rest_state_router
from routers.ws_realtime_router import router as ws_realtime_router
from routers.screenshots_router import router as screenshots_router
from routers.daily_counts_event_router import router as daily_counts_event_router

from services.websocket_services.realtime_manager import realtime_manager
from db.init_db import init_db

# --- TAMBAHAN 1: IMPORT SCHEDULER ---
from services.report.manager.scheduler import start_report_scheduler
from services.report.manager.scheduler_office import start_report_scheduler as start_report_scheduler_office

# --- TAMBAHAN 2: IMPORT SCHEDULER HARIAN ---
from services.report.manager.scheduler_office_daily import start_daily_scheduler as start_report_scheduler_office_daily
# ------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")

    # --- SEND REPORT BY EMAIL USING CRON JOB  ---
    #--- issue SMTP port 587 connection must unlock by firewall ---
    try:
        # start_report_scheduler()
        start_report_scheduler_office()
        # start_report_scheduler_office_daily()
        print("Auto-Report Scheduler is active")
    except Exception as e:
        print(f"Error starting report scheduler: {e}")
    # --------------------------------------

    # REGISTER CAMERA
    realtime_manager.register_camera(
        cam_id="cam1",
        rtsp=os.getenv("CAM_4"),
        p1=(1000, 0),
        p2=(1000, 1450)
    )

    # realtime_manager.register_camera(
    #     cam_id="cam2",
    #     rtsp=os.getenv("CAM_5"),
    #     p1=(1000, 0),
    #     p2=(1000, 1450)
    # )

    # START
    realtime_manager.start_all()

    yield


app = FastAPI(lifespan=lifespan)

# static storage
app.mount(
    "/storage",
    StaticFiles(directory="/storage"),
    name="storage"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL_LAPTOP"),
        os.getenv("FRONTEND_URL"),
        os.getenv("FRONTEND_URL_LOCALHOST")
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

app.include_router(ws_realtime_router)
app.include_router(screenshots_router, prefix="/api")
app.include_router(daily_counts_event_router, prefix="/api")


@app.get("/")
def root():
    return {"status": "YOLO API running"}