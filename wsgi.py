from app import create_app
import os

# Make sure instance directory exists
instance_path = os.path.join(os.getcwd(), 'instance')
os.makedirs(instance_path, exist_ok=True)

app = create_app()

if __name__ == "__main__":
    app.run()
