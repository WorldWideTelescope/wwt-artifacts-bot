import os

from baldrick import create_app

# Configure the App
app = create_app('wwt-artifacts-bot')

# Import plugins
import github_handler
app.register_blueprint(github_handler.azure_artifacts_blueprint)

# Bind to PORT if defined, otherwise default to 5000.
port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port, debug=False)
