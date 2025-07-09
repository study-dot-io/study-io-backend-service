# study-io-backend-service
Python backend service using Flask

## Responsibilities
1. Accepts document uploads
2. Calls LLM to extract key points & generate quiz questions
3. Converts LLM response to JSON
4. Provides API endpoints for mobile app

## Overall flow
1. User uploads document 
2. Handle login using firebase/supabase - returns a JWT token 
3. Backend service receives document and passes to LLM
4. LLM processes and returns a JSON response
   - We should probably store the json response somewhere to avoid calling the LLM for the same file
5. Could use S3/postgres to sync with localstorage
6. Store the file hash
7. JSON response gets sent to mobile app
8. This assumes one document can only make one deck
9. Sync service updates cloud storage with local or vice versa
