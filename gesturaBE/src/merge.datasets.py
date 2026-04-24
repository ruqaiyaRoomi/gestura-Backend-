import pandas as pd

# Load original dataset
df1 = pd.read_csv("data/landmarks.csv")

# Load your custom dataset
df2 = pd.read_csv("data/custom_landmarks.csv")

print("Original shape:", df1.shape)
print("Custom shape:", df2.shape)

# Make sure column names match EXACTLY
df2.columns = df1.columns

# Merge vertically (stack rows)
df_merged = pd.concat([df1, df2], ignore_index=True)

# Save merged dataset
df_merged.to_csv("data/landmarks_merged.csv", index=False)

print("Merged shape:", df_merged.shape)