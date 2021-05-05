sphinx-apidoc -o . ../VyPR
mv VyPR.rst index.rst
make html
echo "Documentation generated."
