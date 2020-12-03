# Dec 03, 2020,  A Simple Scala AKKA Job Scheduling Actor

## The Problem
I wanted to make a simple Scala AKKA hello-world example that was
not trivial, showed at least a skeleton of something useful, but also simple.

The example I settled on was a simple **job scheduler** that could create a new **TaskWorker**, send it a message to start work, and receive
messages about the status of the work of the **Task**.

For completeness the project is built using the following SBT file:
```scala
name := "JobScheduler"
version := "0.1"

scalaVersion := "2.13.2"

val AkkaTypedVersion = "2.6.10"
val AkkaHttpVersion = "10.2.1"

libraryDependencies ++= Seq(
  "com.typesafe.akka" %% "akka-stream" % AkkaTypedVersion,
  "com.typesafe.akka" %% "akka-http" % AkkaHttpVersion,
  "com.typesafe.akka" %% "akka-actor-typed" % AkkaTypedVersion,
)
```

You can omit the HTTP library, but that is quite useful for other things too.

The main app is relatively simple:
```scala
package jobcoordinator

import akka.actor.typed.{ActorSystem}

object Main extends App {
  println("Creating Actor System...")
  val actor = ActorSystem[TaskSchedulerMessage](TaskScheduler(), "task-scheduler")
  actor ! TaskOneRequest("a-task-id")
}
```

This creates the actor system, which accepts messages of type **TaskSchedulerMessage**.
It is a common pattern to create a **trait** for all messages for which an actor is able to receive.

The first set of messages are two abstract **tasks** that I will call "task1" and "task2".

These messages are:
```scala
sealed trait TaskSchedulerMessage;
case class TaskOneRequest(taskId: String) extends TaskSchedulerMessage
case class TaskTwoRequest(taskId: String) extends TaskSchedulerMessage
```

We take some **taskId** as a descriptor, keeping track of the outstanding tasks.
Note that the messages are all **case classes** as they are all immutable and serializable by definition.

The **TaskScheduler** must also **receive** status messages back, so these messages also inherit from that same trait.

```scala
case class TaskStartedResponse(taskId: String) extends TaskSchedulerMessage
case class TaskCompletedResponse(taskId: String) extends TaskSchedulerMessage
```

Now we can introduce the **TaskScheduler**

## Task Scheduler

The imports are simple:
```scala
package jobcoordinator

import akka.actor.typed.Behavior
import akka.actor.typed.javadsl.{ActorContext, Behaviors}
import jobcoordinator.TaskOneWorker.Start
```
The last import defines the message for starting the task.

Creating a Task Scheduler is done with the following object:
```scala
object TaskScheduler {
  def apply() : Behavior[TaskSchedulerMessage] =
    Behaviors.setup[TaskSchedulerMessage](context =>
       new TaskScheduler(context).waitForMessage)
}
```
The **setup** is used to define an actor **behavior**, defined in the class:
```scala
class TaskScheduler(context: ActorContext[TaskSchedulerMessage]) {
  val waitForMessage: Behavior[TaskSchedulerMessage] = {
    Behaviors.receiveMessage[TaskSchedulerMessage] {
      case TaskOneRequest(taskId) => {
        println("Am in task-scheduler waitForMessage")
        val worker = context.spawn(TaskOneWorker(taskId), "task-1")
        worker ! Start(context.getSelf, taskId)
        Behaviors.same
      }
      case TaskStartedResponse(taskId) => {
        println("Got a task started")
        Behaviors.same
      }
      case TaskCompletedResponse(taskId) => {
        println("Got a task completed")
        Behaviors.same
      }
    }
  }
}
```

The scheduler behavior is called **waitForMessage** as it only defines
the behaviors of receiving messags.
For brevity only tasks of type one are supported, but adding more is simple.

The first case-class defines what happens when a **TaskOneRequest** is received:
* A **TaskOneWorker** is spawned, and passed the **taskId** of the message.
* A **Start** message is then passed to the worker.  
A refrence to the **TaskScheduler** is passed using the actor's **context**.
This is used to pass the return status messages.

The other two messages are simple responses to notifications about the starting and completion of the task.

Each of the message cases returns
```scala
Behaviors.same
```
indicating that the behavior of the actor continues to be the same upon returning control to the ActorSystem.
If we wanted to stop the TaskScheduler, we could return
```scala
Behaviors.stopped
```
perhaps as a response to a shutdown message (as it is shown the program will not exit.)

Now let's look at the Worker

### TaskOneWorker
```scala
package jobcoordinator

import akka.actor.typed.{ActorRef, Behavior }
import akka.actor.typed.javadsl.{ ActorContext,  Behaviors }
import jobcoordinator.TaskOneWorker.TaskWorkerCommand

object TaskOneWorker {

  sealed trait TaskWorkerCommand
  case class Start(replyTo : ActorRef[TaskSchedulerMessage],
    args: String) extends TaskWorkerCommand

  def apply(taskId: String): Behavior[TaskWorkerCommand] = {
    Behaviors.setup[TaskWorkerCommand](context => new
        TaskOneWorker(context, taskId).waitForMessage)
  }
}
```
The first part just defines the messages that the worker can handle.
The **Start** message has an **ActorRef** parameter as mentioned earlier.
The **args** field could be anything for running the task -- we are just passing the **taskId**.

```scala
class TaskOneWorker(context : ActorContext[TaskWorkerCommand],
    taskId: String) {

  import TaskOneWorker._

  def run(args: String): Unit = {
  }

  val waitForMessage: Behavior[TaskWorkerCommand] =
    Behaviors.receiveMessage[TaskWorkerCommand] {
      case Start(replyTo, args) => {
        replyTo ! TaskStartedResponse(taskId)
        this.run(args)
        replyTo ! TaskCompletedResponse(taskId)
        Behaviors.same
      }
    }
}
```
The behavior of the worker is simple and consists of:
* Sending a **TaskStartedResponse** message indicating that the task is about to start.
* Running the task - in this case using the **run()** method, that is blank.
* Sending a **TaskCompletedResponse** messsage.

And that's it!
The output demonstrates that the actors are communicating correctly:
```
Creating Actor System...
Am in task-scheduler waitForMessage
Got a task started
Got a task completed
```
