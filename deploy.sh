echo "Building Docker image for Movie Recommender..."

docker build -t movie_recommender .

echo "Docker image for Movie Recommender built successfully."

echo "Saving the image in .tar format..."
docker save movie_recommender -o movie_recommender.tar
echo "Docker image saved as movie_recommender.tar."