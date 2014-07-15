(function() {
  'use strict';
  
  var module = angular.module(
    'communityshare.services.share',
    [
      'communityshare.services.item'
    ]);

  module.factory(
    'Share',
    function(itemFactory, EvntBase, SessionBase) {
      var Share = itemFactory('share');
      Share.prototype.updateFromData = function(shareData) {
        this._baseUpdateFromData(shareData);
        if (this.events) {
          for (var i=0; i<this.events.length; i++) {
            this.events[i] = EvntBase.make(this.events[i]);
          }
        } else {
          this.events = [];
        }
        var iAmCommunityPartner = false;
        var iAmEducator = false;
        if (SessionBase.activeUser) {
          iAmCommunityPartner = (
            SessionBase.activeUser.id === this.community_partner_user_id);
          iAmEducator = (
            SessionBase.activeUser.id === this.educator_user_id);
        }
        if (this.educator && this.community_partner) {
          if (iAmEducator) {
            this.otherUser = this.community_partner;
          } else if (iAmCommunityPartner) {
            this.otherUser = this.educator;
          }
        }
        this.canApprove = false;
        if ((iAmEducator) && (!this.educator_approved) && (this.community_partner_approved)) {
          this.canApprove = true;
        } else if ((iAmCommunityPartner) && (!this.community_partner_approved) && (this.educator_approved)) {
          this.canApprove = true;
        }
        this.approved = (this.educator_approved && this.community_partner_approved);
      };
      Share.prototype.hasActiveEvent = function() {
        var hasEvents = false;
        for (var i=0; i<this.events.length; i++) {
          var evnt = this.events[i];
          if ((evnt.id >= 0) && (evnt.active)) {
            hasEvents = true;
          }
        }
        return hasEvents;
      };
      Share.prototype.addNewEvent = function() {
        var evnt = new EvntBase({
          share_id: this.id,
          title: this.title,
          active: true,
          description: '',
          datetime_start: undefined,
          datetime_stop: undefined
        });
        this.events.push(evnt);
      };
      return Share;
    });

  module.factory(
    'EvntBase',
    function(itemFactory) {
      var Evnt = itemFactory('event');
      return Evnt;
    });

  var splitDateTime = function(datetime) {
    var date = new Date(datetime.getFullYear(),
                        datetime.getMonth(),
                        datetime.getDate());
    var time = new Date(1900, 0, 1,
                        datetime.getHours(),
                        datetime.getMinutes());
    var combined = {
      date: date,
      time: time
    };
    return combined;
  };

  var combineDateTime = function(date, time) {
    var offset = time.getTimezoneOffset();
    var combined = new Date(
      date.getFullYear(),
      date.getMonth(),
      date.getDate(),
      time.getHours(),
      time.getMinutes());
    return combined;
  };

  module.factory(
    'eventLoader',
    function(Evnt, $q) {
      return function(eventId) {
        var deferred = $q.defer();
        var eventPromise = Evnt.get(eventId);
        eventPromise.then(
          function(event) {
            deferred.resolve(event);
          },
          function() {
            deferred.resolve(undefined);
          });
        return deferred.promise;
      }
      
    });

  module.factory(
    'Evnt',
    function(EvntBase, Share) {
      var default_datetime = new Date();
      default_datetime.setHours(0, 0, 0, 0);
      EvntBase.prototype.updateFromData = function(eventData) {
        this._baseUpdateFromData(eventData);
        if (this.datetime_start === undefined) {
          this.datetime_start = default_datetime;
        }
        if (this.datetime_stop === undefined) {
          this.datetime_stop = default_datetime;
        }
        this.datetime_start = new Date(this.datetime_start);
        var split = splitDateTime(this.datetime_start);
        this.date = split.date;
        this.time_start = split.time;
        this.datetime_stop = new Date(this.datetime_stop);
        var split = splitDateTime(this.datetime_stop);
        this.time_stop = split.time;
        if (this.share) {
          this.share = new Share(this.share);
        }
      };
      EvntBase.prototype.updateDateTimes = function() {
        this.datetime_start = combineDateTime(this.date, this.time_start);
        this.datetime_stop = combineDateTime(this.date, this.time_stop);
      };
      return EvntBase;
    });
  
})();
