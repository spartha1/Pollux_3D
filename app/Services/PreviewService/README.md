# Preview Service Setup

## Requirements
- Python 3.10
- Conda package manager

## Installation

1. Create and activate conda environment:
```bash
conda create --name polluxw python=3.10
conda activate polluxw
```

2. Install dependencies:
```bash
conda install -c conda-forge pythonocc-core=7.9.0 numpy vtk pyvista
conda install -c conda-forge fastapi uvicorn pydantic pillow
```

## Configuration

1. Set up environment variables in your Laravel `.env`:
```
PREVIEW_SERVICE_URL=http://localhost:8088
PREVIEW_SERVICE_TIMEOUT=120
```

2. For production, update the URL to match your server configuration.

## Running the Service

### Development
```bash
# Windows
start_preview_server.bat

# Linux/Mac
./start_preview_server.sh
```

### Production
We recommend using a process manager like Supervisor:

1. Install Supervisor
2. Add configuration:
```ini
[program:preview-service]
command=/path/to/conda/envs/polluxw/bin/python /path/to/app/Services/PreviewService/simple_preview_server.py
directory=/path/to/app/Services/PreviewService
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/preview-service.err.log
stdout_logfile=/var/log/preview-service.out.log
```

3. Update Supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start preview-service
```

## Troubleshooting

1. Check logs in `/var/log/preview-service.*.log`
2. Verify conda environment is activated
3. Ensure all dependencies are installed
4. Check file permissions
5. Verify network connectivity and port availability
