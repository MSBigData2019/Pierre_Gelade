package com.sparkProject

import org.apache.spark.SparkConf
import org.apache.spark.ml.Pipeline
import org.apache.spark.ml.classification.LogisticRegression
import org.apache.spark.ml.evaluation.MulticlassClassificationEvaluator
import org.apache.spark.sql.{DataFrame, SparkSession}
import org.apache.spark.ml.feature._
import org.apache.spark.ml.tuning.{ParamGridBuilder, TrainValidationSplit}

object Trainer {

  def main(args: Array[String]): Unit = {

    val conf = new SparkConf().setAll(Map(
      "spark.scheduler.mode" -> "FIFO",
      "spark.speculation" -> "false",
      "spark.reducer.maxSizeInFlight" -> "48m",
      "spark.serializer" -> "org.apache.spark.serializer.KryoSerializer",
      "spark.kryoserializer.buffer.max" -> "1g",
      "spark.shuffle.file.buffer" -> "32k",
      "spark.default.parallelism" -> "12",
      "spark.sql.shuffle.partitions" -> "12",
      "spark.driver.maxResultSize" -> "2g"
    ))

    val spark = SparkSession
      .builder
      .config(conf)
      .appName("TP_spark")
      .getOrCreate()


    /*******************************************************************************
      *
      *       TP 3 - Pierre Gelade
      *
      *       - lire le fichier sauvegarder précédemment
      *       - construire les Stages du pipeline, puis les assembler
      *       - trouver les meilleurs hyperparamètres pour l'entraînement du pipeline avec une grid-search
      *       - Sauvegarder le pipeline entraîné
      *
      *       if problems with unimported modules => sbt plugins update
      *
      ********************************************************************************/

      // Liens
      // Lien vers trainingset
      val path_trainingset = "/home/home/Documents/Spark/prepared_trainingset/"
    // Lien vers le répertoire où enregistrer le modèle entrainé
      val path_model = "/home/home/Documents"


    // a) Chargement du trainingset
    val df: DataFrame = spark
      .read
      .option("header", true)
      .option("inferSchema", "true")
      .parquet(path_trainingset)

    // Stage 1 : Tokenizer
    val tokenizer = new RegexTokenizer()
      .setPattern("\\W+")
      .setGaps(true)
      .setInputCol("text")
      .setOutputCol("tokens")

  //Stage 2 : Stop Words
   val remover: StopWordsRemover = new StopWordsRemover()
     .setInputCol("tokens")
     .setOutputCol("tokens_wsw")

//Stage 3 : TF
    val vectorizer = new CountVectorizer()
      .setInputCol("tokens_wsw")
      .setOutputCol("tf")

// Stage 4 : IDF
     val idf = new IDF()
       .setInputCol("tf")
       .setOutputCol("tfidf")

// Stage 5 : Conversion variables categorielles -> numériques (country2)
      val Co_indexer = new StringIndexer()
        .setInputCol("country2")
        .setOutputCol("country_indexed")

    // Stage 6 : Conversion variables categorielles -> numériques (currency2)
      val Cu_indexer = new StringIndexer()
        .setInputCol("currency2")
        .setOutputCol("currency_indexed")

    // Stage 7 : OneHotEncoder (country)
      val Co_onehotenc = new OneHotEncoder()
        .setInputCol("country_indexed")
        .setOutputCol("country_onehot")

    // Stage 8 : OneHotEncoder (currency)
    val Cu_onehotenc = new OneHotEncoder()
      .setInputCol("currency_indexed")
      .setOutputCol("currency_onehot")

    // Stage 9 : Assemblage des features
    val assembler = new VectorAssembler()
      .setInputCols(Array("tfidf", "days_campaign", "hours_prepa", "goal", "country_onehot", "currency_onehot"))
      .setOutputCol("features")

    // Stage 10 : modèle de classification (régression logistique)
    val lr = new LogisticRegression()
      .setElasticNetParam(0.0)
      .setFitIntercept(true)
      .setFeaturesCol("features")
      .setLabelCol("final_status")
      .setStandardization(true)
      .setPredictionCol("predictions")
      .setRawPredictionCol("raw_predictions")
      .setThresholds(Array(0.7, 0.3))
      .setTol(1.0e-6)
      .setMaxIter(300)

    // Creation du pipeline
    val pipeline = new Pipeline()
      .setStages(Array(tokenizer, remover,vectorizer,idf,Co_indexer,Cu_indexer,Co_onehotenc,Cu_onehotenc,assembler, lr))

    // Creation des df train et test
    val Array(training, test) = df.randomSplit(Array(0.9, 0.1), seed=10)

    // Préparation de la grid-search
    val paramGrid = new ParamGridBuilder()
      .addGrid(lr.regParam, Array(10e-8, 10e-6, 10e-4, 10e-2))
      .addGrid(vectorizer.minDF, Array(55.0, 75.0, 95.0))
      .build()

    //f1=0.662
    //.addGrid(lr.regParam, Array(10e-8, 10e-6, 10e-4, 10e-2))
    //.addGrid(vectorizer.minDF, Array(35.0, 45.0, 55.0))

    // Choix de l'évaluateur
    val evaluator = new MulticlassClassificationEvaluator()
      .setMetricName("f1")
      .setLabelCol("final_status")
      .setPredictionCol("predictions")

    // Lancement de la grid-search sur le dataset “training”
    val trainValidationSplit = new TrainValidationSplit()
      .setEstimator(pipeline)
      .setEvaluator(evaluator)
      .setEstimatorParamMaps(paramGrid)
      .setTrainRatio(0.7)
    val model = trainValidationSplit.fit(training)

    // Predictions sur test
    val df_WithPredictions = model.transform(test)

    // f1_score
    val f1_score = evaluator.evaluate(df_WithPredictions)
    println("Valeur de F1 : " + f1_score)

    // Affichage
    df_WithPredictions.groupBy("final_status", "predictions").count.show()

    // Sauvegarde du modèle entraîné
    model.write.overwrite().save(path_model + "/model")


  }
}
