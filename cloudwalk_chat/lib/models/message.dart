enum Sender { user, bot }

class Message {
  final Sender from;
  final String text;
  Message(this.from, this.text);
}
