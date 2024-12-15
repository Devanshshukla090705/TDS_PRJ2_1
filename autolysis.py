import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import openai
from tenacity import retry, stop_after_attempt, wait_fixed

# Ensure the AIPROXY_TOKEN is retrieved from environment variables
try:
    AIPROXY_TOKEN = os.environ["AIPROXY_TOKEN"]
except KeyError:
    raise EnvironmentError(
        "AIPROXY_TOKEN environment variable not set. Please set it before running the script."
    )

# Set the AI Proxy URL
AIPROXY_URL = "https://aiproxy.sanand.workers.dev/openai/v1"

# Configure OpenAI client settings to use AI Proxy URL
openai.api_base = AIPROXY_URL
openai.api_key = AIPROXY_TOKEN  # Use the AIPROXY_TOKEN as the API key

# Function to Load Dataset
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def load_dataset(file_path):
    """Loads the dataset from the provided CSV file."""
    try:
        data = pd.read_csv(file_path)
        print("Dataset loaded successfully.")
        return data
    except Exception as e:
        print(f"Error loading dataset: {e}")
        raise

# Function to Analyze Data
def analyze_data(data):
    """Generates basic statistics and analysis from the dataset."""
    analysis = {
        "shape": data.shape,
        "columns": data.dtypes.to_dict(),
        "missing_values": data.isnull().sum().to_dict(),
        "summary_stats": data.describe(include='all').to_dict()
    }
    return analysis

# Function to Generate Visualizations
def create_visualizations(data, output_dir):
    """Generates visualizations like a correlation heatmap from the dataset."""
    numeric_data = data.select_dtypes(include=['number'])

    if numeric_data.empty:
        print("No numeric columns available for correlation heatmap.")
        return

    # Example: Correlation heatmap
    plt.figure(figsize=(10, 8))
    sns.heatmap(numeric_data.corr(), annot=True, cmap="coolwarm")
    plt.title("Correlation Heatmap")
    plt.savefig(f"{output_dir}/correlation_heatmap.png")
    plt.close()

# Function to Interact with LLM
def ask_llm(prompt):
    """Interacts with the LLM through the AI Proxy"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a data analyst."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message["content"]
    except Exception as e:
        print(f"Error communicating with LLM: {e}")
        return "No insights generated due to an error in LLM communication."

# Function to Write README File
def write_readme(analysis, insights, output_dir):
    """Writes the analysis and insights into a README.md file."""
    if insights is None:
        insights = "No insights generated due to an error in LLM communication."
    with open(f"{output_dir}/README.md", "w") as f:
        f.write("# Automated Analysis\n\n")
        f.write("## Summary\n")
        f.write(f"- Shape: {analysis['shape']}\n")
        f.write("- Missing Values:\n")
        for col, val in analysis['missing_values'].items():
            f.write(f"  - {col}: {val}\n")
        f.write("\n## Insights\n")
        f.write(insights)

# Main Function to Integrate Everything
def main(file_path, output_dir):
    """Main function to run the analysis, visualizations, and write the README file."""
    # Load the dataset
    data = load_dataset(file_path)

    # Analyze the data
    analysis = analyze_data(data)
    print("Analysis completed.")

    # Generate visualizations
    create_visualizations(data, output_dir)
    print("Visualizations generated.")

    # Interact with LLM to get insights
    prompt = f"""
Based on the following analysis and visualizations, provide insights:
- Summary Statistics: {analysis['summary_stats']}
- Visualizations: [Insert chart descriptions or file paths]
"""
    insights = ask_llm(prompt)
    print("Insights generated by LLM.")

    # Write the README file
    write_readme(analysis, insights, output_dir)

if __name__ == "__main__":
    # Ensure proper command-line arguments
    import sys
    if len(sys.argv) != 3:
        print("Usage: python autolysis.py <input_csv_path> <output_dir>")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_directory = sys.argv[2]

    # Ensure output directory exists
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Run the main function
    main(input_csv, output_directory)
