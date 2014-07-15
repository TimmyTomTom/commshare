(function() {
  'use strict';
  var app = angular.module(
    'communityshare',
    [
      'ngRoute',
      'ui.bootstrap',
      'communityshare.directives.mainview',
      'communityshare.controllers.authentication',
      'communityshare.controllers.home',
      'communityshare.controllers.user',
      'communityshare.controllers.search',
      'communityshare.controllers.message',
      'communityshare.controllers.share',
      'communityshare.directives.labels',
      'communityshare.services.share'
    ]);
  
  app.config(function($routeProvider) {

    $routeProvider.when('/', {
      templateUrl: './static/templates/default.html',
      controller: 'DefaultController',
      resolve: {
        user: function(activeUserLoader) {
          return activeUserLoader();
        }
      }
    });

    $routeProvider.when('/login', {
      templateUrl: './static/templates/login.html',
      controller: 'LoginController'
    });

    $routeProvider.when('/logout', {
      templateUrl: './static/templates/logout.html',
      controller: 'LogoutController'
    });

    $routeProvider.when('/signup/communitypartner', {
      templateUrl: './static/templates/signup_community_partner.html',
      controller: 'SignupCommunityPartnerController'
    });

    $routeProvider.when('/signup/educator', {
      templateUrl: './static/templates/signup_educator.html',
      controller: 'SignupEducatorController'
    });

    $routeProvider.when('/requestresetpassword', {
      templateUrl: './static/templates/request_reset_password.html',
      controller: 'RequestResetPasswordController'
    });

    $routeProvider.when('/resetpassword', {
      templateUrl: './static/templates/reset_password.html',
      controller: 'ResetPasswordController'
    });

    $routeProvider.when('/confirmemail', {
      templateUrl: './static/templates/confirm_email.html',
      controller: 'ConfirmEmailController'
    });

    $routeProvider.when('/home', {
      templateUrl: './static/templates/home.html',
      controller: 'HomeController',
      resolve: {
        activeUser: function(activeUserLoader) {
          return activeUserLoader();
        }
      }
    });

    $routeProvider.when('/searchusers', {
      templateUrl: './static/templates/search_users.html',
      controller: 'SearchUsersController',
      resolve: {
        activeUser: function(activeUserLoader) {
          return activeUserLoader();
        }
      }
    });

    $routeProvider.when('/settings', {
      templateUrl: './static/templates/settings.html',
      controller: 'SettingsController',
      resolve: {
        activeUser: function(activeUserLoader) {
          return activeUserLoader();
        }
      }
    });

    $routeProvider.when('/user/:userId', {
      templateUrl: './static/templates/user_view.html',
      controller: 'UserController',
      resolve: {
        activeUser: function(activeUserLoader) {
          return activeUserLoader();
        }
      }
    });

    $routeProvider.when('/search/:searchId/edit', {
      templateUrl: './static/templates/search_edit.html',
      controller: 'SearchEditController',
      resolve: {
        activeUser: function(activeUserLoader) {
          return activeUserLoader();
        }
      }
    });

    $routeProvider.when('/search/:searchId/results', {
      templateUrl: './static/templates/search_results.html',
      controller: 'SearchResultsController',
      resolve: {
        activeUser: function(activeUserLoader) {
          return activeUserLoader();
        }
      }
    });

    $routeProvider.when('/search', {
      templateUrl: './static/templates/search_edit.html',
      controller: 'SearchEditController',
      resolve: {
        activeUser: function(activeUserLoader) {
          return activeUserLoader();
        }
      }
    });

    $routeProvider.when('/conversation/unviewed', {
      templateUrl: './static/templates/unviewed_conversations.html',
      controller: 'UnviewedConversationController',
      resolve: {
        activeUser: function(activeUserLoader) {
          return activeUserLoader();
        }
      }
    });

    $routeProvider.when('/events', {
      templateUrl: './static/templates/events.html',
      controller: 'EventsController',
      resolve: {
        activeUser: function(activeUserLoader) {
          return activeUserLoader();
        }
      }
    });

    $routeProvider.when('/event/:eventId', {
      templateUrl: './static/templates/event_view.html',
      controller: 'EventController',
      resolve: {
        activeUser: function(activeUserLoader) {
          return activeUserLoader();
        },
        evnt: function(eventLoader, $route) {
          return eventLoader($route.current.params.eventId);
        }
      }
    });

    $routeProvider.when('/conversation/:conversationId', {
      templateUrl: './static/templates/conversation.html',
      controller: 'ConversationController',
      resolve: {
        activeUser: function(activeUserLoader) {
          return activeUserLoader();
        },
        conversation: function(conversationLoader, $route) {
          return conversationLoader($route.current.params.conversationId);
        }
      }
    });

    $routeProvider.when('/share/new', {
      templateUrl: './static/templates/share_edit.html',
      controller: 'NewShareController',
      resolve: {
        activeUser: function(activeUserLoader) {
          return activeUserLoader();
        }
      }
    });

    $routeProvider.when('/share/:shareId', {
      templateUrl: './static/templates/share.html',
      controller: 'ShareController',
      resolve: {
        activeUser: function(activeUserLoader) {
          return activeUserLoader();
        }
      }
    });

    $routeProvider.otherwise({
      templateUrl: './static/templates/unknown.html'
    });
    
  });
  
})();
