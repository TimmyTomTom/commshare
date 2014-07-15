(function() {
  'use strict';
  
  var module = angular.module(
    'communityshare.controllers.conversation',
    [
      'communityshare.services.authentication',
      'communityshare.services.utility',
      'communityshare.services.conversation'
    ]);

  var combineMessages = function(baseMessage, specificMessage) {
    var msg = '';
    if (specificMessage) {
      msg = ': ' + specificMessage;
    }
    var message = baseMessage + msg;
    return message;
  };

  module.controller(
    'ConversationController',
    function($scope, $q, $location, $timeout, $modal, Session,
             Conversation, Message, User, Share, makeDialog, conversation) {
      $scope.Session = Session;
      if ((conversation === undefined) || (Session.activeUser === undefined)) {
        return;
      }
      var sharesPromise = Share.get_many({conversation_id: conversation.id});
      $scope.otherUser = undefined;
      $scope.conversation = conversation;
      $scope.newMessage = undefined;
      var makeNewMessage = function() {
        var newMessage = new Message({
          conversation_id: conversation.id,
          sender_user_id: Session.activeUser.id,
          content: ''
        });
        return newMessage;
      };
      var showErrorMessage = function(message) {
        var baseMessage = 'Failed to load conversation';
        var msg = combineMessages(baseMessage, message);
        $scope.errorMessage = msg;
      };
      var refreshConversation = function() {
        var refreshedConversationPromise = Conversation.get(conversation.id);
        refreshedConversationPromise.then(
          function(conversation) {
            $scope.conversation = conversation;
            $timeout(refreshConversation, 5000);
            $scope.errorMessage = '';
          },
          showErrorMessage
        );
      };
      conversation.markMessagesAsViewed();
      if (conversation.userA.id === Session.activeUser.id) {
        $scope.otherUser = conversation.userB;
      } else {
        $scope.otherUser = conversation.userA;
      }
      $scope.messageHighlightClasses = {};
      $scope.messageHighlightClasses[Session.activeUser.id] = 'highlight1';
      $scope.messageHighlightClasses[$scope.otherUser.id] = 'highlight2';
      $scope.newMessage = makeNewMessage();
      $timeout(refreshConversation, 5000);
      sharesPromise.then(
        function(shares) {
          shares.sort(function(a, b) { return a.id - b.id; });
          if (conversation.otherUser) {
            if ((shares.length === 0)) {
              $scope.share = conversation.makeShare();
              $scope.events = $scope.share.events;
            } else {
              $scope.share = shares[0];
              if ($scope.share.events.length === 0) {
                $scope.share.addNewEvent();
              }
              $scope.events = $scope.share.events;
            }
          } else {
            if (shares) {
              $scope.share = shares[0];
            }
          }            
        },
        showErrorMessage
      );
      $scope.sendMessage = function() {
        var messagePromise = $scope.newMessage.save();
        messagePromise.then(
          function(message) {
            message.sender_user = Session.activeUser;
            $scope.conversation.messages.push(message);
            $scope.newMessage = makeNewMessage();
          },
          showErrorMessage
        );
      };
      $scope.editShare = function() {
        var opts = {
          templateUrl: './static/templates/share_edit.html',
          controller: 'EditShareController',
          resolve: {
            share: function() {return $scope.share;},
          }
        };
        var m = $modal.open(opts);
      };
      $scope.now = new Date();
      $scope.reviewEvent = function(event) {
        $location.path('/event/' + event.id);
      };
      $scope.confirmShare = function() {
        // Saving with no changes acts as an approve.
        $scope.share.save();
      };
      $scope.cancelShare = function() {
        var title = 'Cancel Share';
        var msg = 'Do you really want to cancel this share with ' +
          $scope.otherUser.name;
        var btns = [{result:'yes', label: 'Yes', cssClass: 'btn-primary'},
                    {result:'no', label: 'No'}];
        var d = makeDialog(title, msg, btns);
        d.result.then(
          function(result) {
            if (result === 'yes') {
              // FIXME: Send email to otherUser saying they want to cancel it.
              var deletePromise = $scope.share.destroy();
              deletePromise.then(
                function() {
                  $scope.share = conversation.makeShare();
                  $scope.events = $scope.share.events;
                },
                function(message) {
                  var baseMessage = 'Failed to cancel share';
                  var msg = combineMessages(baseMessage, message);
                  $scope.errorMessage = msg;
                });
            }
          });
      };
    });
  
  module.controller(
    'NewConversationController',
    function (Session, $scope, $modalInstance, userId, searchId, User,
              Conversation, Message, Authenticator, Messages) {
      var userPromise = User.get(userId);
      $scope.Session = Session;
      $scope.errorMessage = '';
      if (!Session.activeUser.email_confirmed) {
        // Refresh active User to make sure email is still unconfirmed.
        User.get(Session.activeUser.id, true);
      }
      $scope.conversation = new Conversation({
        title: undefined,
        search_id: searchId,
        userA_id: Session.activeUser.id,
        userB_id: userId
      });
      $scope.resendEmailConfirmation = function() {
        var emailConfirmPromise = Authenticator.requestConfirmEmail();
        emailConfirmPromise.then(
          function() {
            Messages.info('Sent email confirmation email.');
          },
          function(errorMessage) {
            Messages.error(errorMessage);
          });
      };
      $scope.message = new Message({
        conversation_id: undefined,
        sender_user_id: Session.activeUser.id,
        content: undefined
      });
      userPromise.then(
        function(user) {
          $scope.user = user;
        });
      $scope.cancel = function() {
        $modalInstance.close();
      };
      $scope.startConversation = function() {
        var conversationPromise = $scope.conversation.save();
        conversationPromise.then(
          function(conversation) {
            $scope.errorMessage = '';
            $scope.message.conversation_id = conversation.id;
            var messagePromise = $scope.message.save();
            messagePromise.then(
              function(message) {
                $modalInstance.close(conversation);
              },
              function(message) {
                var baseMessage = 'Failed to save message';
                $scope.errorMessage = combineMessages(baseMessage, message);
              });
          },
          function(message) {
            var baseMessage = 'Failed to save conversation';
            $scope.errorMessage = combineMessages(baseMessage, message);
          });
      };
    });

  module.controller(
    'UnviewedConversationController',
    function($scope, $location, Session, Conversation) {
      var conversationsPromise = Conversation.getUnviewedForUser(
        Session.activeUser.id);
      $scope.infoMessage = 'Loading conversations...';
      conversationsPromise.then(
        function(conversations) {
          $scope.conversations = conversations;
          
          $scope.infoMessage = '';
        },
        function(message) {
          var baseMessage = 'Failed to load conversations';
          $scope.errorMessage = combineMessages(baseMessage, message);
          $scope.infoMessage = '';
        });
      $scope.viewConversation = function(conversation_id) {
        $location.path('/conversation/' + conversation_id);
      };
    });

}());
