#\!/bin/bash
API_ID="p0lkqwkiy4"
REGION="us-west-2"

# Enable CORS for /sessions POST
aws apigateway update-method \
  --rest-api-id $API_ID \
  --resource-id mc344h \
  --http-method POST \
  --patch-operations \
    op=add,path=/responseParameters/method.response.header.Access-Control-Allow-Origin,value="'*'" \
  --region $REGION

# Enable CORS for /sessions GET  
aws apigateway update-method \
  --rest-api-id $API_ID \
  --resource-id mc344h \
  --http-method GET \
  --patch-operations \
    op=add,path=/responseParameters/method.response.header.Access-Control-Allow-Origin,value="'*'" \
  --region $REGION

# Update integration responses to map headers
aws apigateway put-integration-response \
  --rest-api-id $API_ID \
  --resource-id mc344h \
  --http-method POST \
  --status-code 201 \
  --response-parameters '{"method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'"}' \
  --region $REGION

aws apigateway put-integration-response \
  --rest-api-id $API_ID \
  --resource-id mc344h \
  --http-method GET \
  --status-code 200 \
  --response-parameters '{"method.response.header.Access-Control-Allow-Origin":"'"'"'*'"'"'"}' \
  --region $REGION

# Deploy changes
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name dev \
  --description "Enable CORS" \
  --region $REGION

echo "CORS enabled and API deployed"
