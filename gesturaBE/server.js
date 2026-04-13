const express = require("express");
const MongoClient = require("mongodb").MongoClient;
const ObjectID = require("mongodb").ObjectID;
var fs = require("fs");
const {spawn} = require("child_process")


var path = require("path");
const app = express();

const pythonProcess = spawn('python3', ['src/predict_api.py'])
let pendingResolve = null

app.use(express.json());
app.set("port", 3000);

// CORS set up
app.use((req, res, next) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Credentials", "true");
  res.setHeader("Access-Control-Allow-Methods", "GET,HEAD,OPTIONS,POST,PUT");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");

  

  next();
});


const uri = "mongodb+srv://ruqaiyah:RR1026@ug.9ogfhhl.mongodb.net/?appName=UG";
const client = new MongoClient(uri);


app.post('/gestura/signUp', SignUp)

app.post("/gestura/login", login); 

app.post('/gestura/quizHistory', saveQuizHistory);

app.get('/gestura/quizHistory', getHistory)

app.post('/gestura/predict', prediction)


app.post('/gestura/userStats', postUserStats)
app.get('/gestura/userStats/:userId', getUserStats)

 
async function startServer() {
  try {
    await client.connect();
    db = client.db("gestura");

    console.log("Connected to MongoDB");

    app.listen(app.get("port"), () => {
      console.log(`Server running on port ${app.get("port")}`);
    });

  } catch (err) {
    console.error(err);
  }
}

startServer();


app.use(function (req, res, next) {
  console.log("in comes a " + req.method + " to " + req.url);
  next();
});

// register a new users
async function SignUp(request, response) {
  let collection = db.collection("userInfo")
    try {
          let userInfo = request.body;
          console.log("Data received: " + JSON.stringify(userInfo));

      
          if (!userInfo.firstName || !userInfo.lastName || !userInfo.email || !userInfo.password) {
              return response.status(400).send({
                  registration: false, 
                  message: "All fields are required.",
              });
          }

        
          const user = await collection.findOne({
              $or: [{ email: userInfo.email }],
          }); 

          if (!user) {
            const insertResult = await collection.insertOne({
            firstName: userInfo.firstName,
            lastName: userInfo.lastName,
            email: userInfo.email,
            password: userInfo.password
    })

    response.send({
        registration: true,
        _id: insertResult.insertedId,
        firstName: userInfo.firstName,
        lastName: userInfo.lastName,
        email: userInfo.email
    })
} else {
    response.send({
        registration: false,
        message: "Email already exists."
    })
}}
   catch (error) {
        console.error("Error during registration:", error);
        response.status(500).send({
            registration: false,
            message: "An error occurred during registration.",
        });
    }
}

async function login(request, response) {
   let collection = db.collection("userInfo")
    let userInfo = request.body;

    
    const user = await collection.findOne({
        email: userInfo.email,
        password: userInfo.password,
    });

    if (user) {
      
        response.send({
            login: true,
            _id: user._id,
            firstName: user.firstName,
            lastName: user.lastName,
            email: user.email
            
         
        });
    } else {
        response.send(
            {
              login: false,
              message:"Username or password incorrect."
            }
        );
    }
}


async function saveQuizHistory(request, response) {
   let collection = db.collection('quizHistory')
    
    try {
        
      const quizData = request.body
      
        const newQuiz = {
            userId: quizData.userId,
            score: quizData.score,
            numberOfQuestions: quizData.numberOfQuestions,
            time: quizData.time,
            accuracy: quizData.accuracy, 
            results: quizData.results, 
            dateTaken: new Date(),
        };
     
       await collection.insertOne(newQuiz);
        response.json({
            saved: true,
            message: 'quiz history saved'
        });
    } catch (error) {
        console.error('Error posting content:', error);
        response.status(500).json({ 
          posted: false, 
          message: 'An error occurred while saving.' 
        }
        );
    }
}

async function postUserStats(request, response) {
  const collection = db.collection('userStats');
  const { userId, module, letter, word} = request.body

  if(!userId ||!module ) {
    return response.status(400).json({
      saved: false,
      message: "missing data"
    })
  }

  const value = letter || word

  try {
    let userStats = await collection.findOne({userId})

    if(!userStats) {
      const newModules = {};

      newModules[module] = value ? [value] : []

      await collection.insertOne ({
        userId,
        modules: 
          newModules
      
      });

      return response.json(
        {saved: true, 
        completed: newModules[module]}
      )

    }  

    if(!userStats.modules)
      userStats.modules = {}
    if(!userStats.modules[module])
      userStats.modules[module] = []

    let updated = false

    if(value && !userStats.modules[module].includes(value)) {
      userStats.modules[module].push(value)
      updated = true
    }

    if(updated) {
      await collection.updateOne(
      {userId},
      {$set: {
        modules: userStats.modules
      }}
    )
    }

    return response.json({
      saved: true,
      completed: userStats.modules[module]
    })
} catch(err) {
  console.error('Error saving progress:', err)
  response.status(500).json({
    saved: false,
    message: 'server error'
  })
}
}

async function getUserStats(request, response) {
  const {userId} = request.params;
  const collection = db.collection('userStats');

  try {
    const userStats = await collection.findOne({userId});
    if(!userStats) {
      return response.status(404).json({message: 'User stats not found'})
    }
    response.json(userStats);
  } catch (err) {
    console.error('Error fetching user stats:', err)
    response.status(500).json({message: 'server error'})
  }
  
}


async function getHistory(request, response) {
  let collection = db.collection('quizHistory')
    try {
      const userId =  request.query.userId
        const quiz = await collection.find({userId: userId}).toArray();
        response.status(200).json(quiz);
    } catch (error) {
        console.error("Error fetching quiz history:", error);
        response.status(500).json({ error: "Failed to fetch history." });
    }
}


pythonProcess.stdout.on('data', (data) => {
  if(pendingResolve) {
    try{
      pendingResolve(JSON.parse(data.toString()))
    } catch (e){
      pendingResolve({err: 'parse errror'})
    }
    pendingResolve = null
  }
})

pythonProcess.stderr.on('data', (data) => {
  console.error('Python error: ', data.toString())
})

const queue = []
let isProcessing = false

function predictLandmarks(landmarks, is_left) {
  return new Promise((resolve) => {
    pendingResolve = resolve
    pythonProcess.stdin.write(JSON.stringify({ landmarks, is_left}) + '\n')
  })
}

async function prediction(request, response) {
  const { landmarks, is_left} = request.body

  try{
    const results = await predictLandmarks(landmarks, is_left)
    response.json(results)
  } catch (err) {
    response.status(500).json({ error: 'prediction failed'})
  } 
  
}

