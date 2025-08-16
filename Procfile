
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --preload
worker: python -c "print('Worker process ready')"
