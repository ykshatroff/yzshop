/*
 *
 *
 * NOTE #1: after an element is set up, assign it the CSS class .yzadmin-setup,
 *      to avoid repeating its setup
 * NOTE #2: Global AJAX success callback will call YzAdmin.onHTMLLoad
 */
(function($) {

    if (! window.console) {
        window.console = console = {
            log: function(msg) {}
        }
    }

    window.YzAdmin = {
        //
        _htmlLoadCallbacks: [],
        _last: null // dummy entry
    }

    YzAdmin.setupTabs = function() {
        // TODO confirm opening tab if current tab not saved
        $("#yzadmin-tabs a").click(function(){
            console.log("tab " + this.id);
            if ($(this).hasClass('current')) {
                // do nothing for current tab
                return false;
            }

            // unset current tabs
//             var currentTabName = currentTab.attr('id').replace('tab-title-', '');
//             var currentTabDiv = $("#tab-" + currentTabName);
            var currentTab = $("#yzadmin-tabs a.current");
            currentTab.removeClass("current");
            $('#yzadmin-tabs ~ div').hide();

            // go on with new tabs
            // new tab = $(this)
            var newTabName = this.id.replace('tab-title-', '');
            var newTabDiv = $("#tab-" + newTabName);
            if (newTabDiv.length) {
                // already loaded
                console.log("tab exists: " + newTabName);
                newTabDiv.show();
            // added --->>>
            // to refresh tabs each time
                newTabDiv.remove();
            }
            if (false) {
            // --->>>

            } else {
                // create an empty tab with loading sign
                // also prevent occasionally adding a tab many times
                var tmp_tab = $('#yzadmin-tmp-tab')
                if (! tmp_tab.length) {
                    tmp_tab = $("<div id='yzadmin-tmp-tab' class='ajax-loading'/>")
                        .insertAfter($('#yzadmin-tabs'));
                }
                $(document).ajaxError(function(evt, rq, conf, ex) {
                    $.jGrowl("AJAX Request Error: " + (ex||rq.status));
                })
                $.get(this.href, function(response) {
                    console.log("fetched tab: " + newTabName);
                    tmp_tab.replaceWith(response);
                    //$("#item-tabs").append(response);
                    YzAdmin.onHTMLLoad();
                })
            }
            $(this).addClass("current");
            return false;
        })
        return YzAdmin;
    }

    YzAdmin.setupDialogLinks = function() {
        $('a.with-dialog').click(function() {
            title = $(this).attr('title') || $(this).text();
            YzAdmin.openDialog($(this).attr('href'), title);
            return false;
        })
        return YzAdmin;
    }

    YzAdmin.setupOverrideFields = function() {
        $(".OverrideFormField").each(function(){
            var field_name = this.id.match(/^field-own_(.*)/)[1];
            console.log(field_name);
            var field_label = $(this).find("label");
            var targetField = $(this).next();
            var wrapper = $("<fieldset></fieldset>");
            wrapper.replaceAll($(this));
//             $(this).wrap(wrapper);
            var legend = $("<legend/>").text(field_label.text());
            wrapper.append(legend);
            wrapper.append(this);
            wrapper.append(targetField);
            field_label.text("Ввод собственного значения");
            var input = $(this).find('input').get(0);
            var override = input.checked;
            var targetFieldInput = targetField.find("input, select, textarea");
            if (! override) {
                targetFieldInput.attr("disabled", "disabled");
            }
            $(input).change(function() {
                if (this.checked) {
                    targetFieldInput.removeAttr("disabled");
                } else {
                    targetFieldInput.attr("disabled", "disabled");
                }
            });
        });
        return YzAdmin;
    }

    YzAdmin.setupSlugFields = function() {
        // apply urlify to name field accompanied by a slug field
        // in general, assert that there is only one such field per page,
        // and per all tabs on that page
        // otherwise, the following would be quite wrong
        $('input[name=name]:not(.yzadmin-setup)').each(function() {
            var _slug = this.form.slug;
            if (_slug) {
                var _name = $(this);
                _name
                    .addClass('yzadmin-setup')
                    .keyup(function() {
                        $(_slug).val(URLify(_name.val()));
                    });
            }
        });
        return YzAdmin;
    }

    YzAdmin.setupDateFields = function() {
        var datefields = $("input.yzadmin-calendar:not(.yzadmin-setup)");
        if (datefields.length > 0) {
            if (! $.datepicker.regional[ LANG ]) {
                $.getScript(STATIC_URL + "js/contrib/jquery-ui/i18n/jquery.ui.datepicker-"
                    + LANG + ".min.js", function() {
                        $.datepicker.setDefaults( $.datepicker.regional[ LANG ] );
                    });
            }

            datefields
                .addClass("yzadmin-setup")
                .datepicker();
        }
        return YzAdmin;
    }

    YzAdmin.setupTextFields = function() {
        var textfields = $("textarea.yzadmin-tinymce:not(.yzadmin-setup)");
        if (textfields.length > 0) {
            $.getScript(
                window.STATIC_URL + "js/contrib/tiny_mce/jquery.tinymce.js",
                function() {
                    textfields
//                         .wrap($("<div class='yzadmin-tinymce-wrapper'/>"))
                        .addClass("yzadmin-setup")
                        .tinymce({
                            // Location of TinyMCE script
                            script_url : STATIC_URL + "js/contrib/tiny_mce/tiny_mce.js",
                            language: window.LANG || "en",
//                             height: "100%",
                            plugins: 'imageupload',
                            relative_urls : false,
                            theme : "advanced",
                            theme_advanced_buttons2_add : "imageupload",
                            theme_advanced_resizing : true,
//                             width: "100%",
                            _last: null
                        });
                }
            );
        }
        return YzAdmin;
    }

    YzAdmin.setupFormFields = function() {
        YzAdmin.setupSlugFields();
        YzAdmin.setupOverrideFields();
        YzAdmin.setupDateFields();
        YzAdmin.setupTextFields();
        return YzAdmin;
    }

    YzAdmin.setupFormCallback = function() {
        // make all forms submissible via AJAX
        // in general, assert that re-applying this to a form won't harm
        $("form:not(.yzadmin-setup)")
            .addClass('yzadmin-setup')
            .ajaxForm({
                success: function(response) {
                    YzAdmin.parseAjaxResponse(response);
                    // re-apply callbacks setup to newly fetched HTML
                    YzAdmin.setupFormCallback();
                    YzAdmin.setupFormFields();
                }
                //error: function(response) { $.jGrowl(response) }
            });
        return YzAdmin;
    }

    YzAdmin.setupPageCallback = function() {
        // set up page changes
        $("#yzadmin-page-navigation a:not(.yzadmin-setup)")
            .addClass('yzadmin-setup')
            .click(function() {
                $.get($(this).attr("href"), function(response) {
                    $("#yzadmin-page").replaceWith(response);
                    // re-setup callback on new HTML
                    YzAdmin.setupPageCallback();
                });
                return false;
            })
        return YzAdmin;
    }

    YzAdmin.setupCategoryToggle = function() {
        //
        $("#cat-0 a.choice:not(.yzadmin-setup)")
            .addClass('yzadmin-setup')
            .click(function() {
                var a = this;
                var action = a.className.match(/off/) ? 'add' : 'remove';
                $.get($(this).attr("href"),
                    { action: action },
                    function(response) {
                        $(a).replaceWith(response);
                        YzAdmin.setupCategoryToggle();
                    }
                )
                return false
            })
        return YzAdmin;
    }

    YzAdmin.displayHTMLMessages = function(context) {
        // handle the html messages
        context = context ? $(context) : $("body");
        var msgElements = context.filter("ul#yzadmin-messages");
        if (msgElements.length == 0) {
            msgElements = context.find("ul#yzadmin-messages");
        }
        if (msgElements.length > 0) {
            msgElements.find("li").each(function(){
                $.jGrowl($(this).text());
            })
            msgElements.remove();
        }
        return context; //.not("ul#yzadmin-messages").find(":not(ul#yzadmin-messages)")
    }

    YzAdmin.onHTMLLoad = function() {
        // execute each time any HTML content is loaded
        // via AJAX or as a complete page

        YzAdmin.setupDialogLinks();

        // set up urlify for slug fields
        YzAdmin.setupFormFields();

        // set up ajax form submit via jquery.form
        YzAdmin.setupFormCallback();

        // set up ajax page navigation
        YzAdmin.setupPageCallback();

        YzAdmin.displayHTMLMessages();
    }

    YzAdmin.beforeAjaxSendCallback = function() {
        console.log("Before AJAX send");
    }

    YzAdmin.AjaxCompleteCallback = function(XMLHttpRequest, textStatus) {
        console.log("AJAX complete: " + textStatus);
    }

    YzAdmin.AjaxErrorCallback = function(XMLHttpRequest, textStatus) {
        console.log("AJAX error: " + textStatus);
        $.jGrowl("AJAX request error!");
        YzAdmin.displayHTMLMessages(XMLHttpRequest.responseText);
    }

    YzAdmin.AjaxSuccessCallback = function(data, textStatus) {
        console.log("AJAX success: " + textStatus);
    }

    YzAdmin.ajaxEval = function(data) {
        // eval all scripts contained in data
        // NOTE: (jquery BUG?) when doing $(context), jquery puts script tags to top level
        //      of the context
        // return the data w/o scripts
        $(data).filter("script").each(function() {
            try {
                $(this).appendTo($("head"));
            } catch (ex) {
                console.log(ex);
            }
        })
        return $(data).not("script");
    }

    YzAdmin.parseAjaxResponse = function(response) {
        // handle response's messages and scripts
        response = $(response);
        response = YzAdmin.ajaxEval(response);
        response = YzAdmin.displayHTMLMessages(response);

        if (response.length) {
            response = response.eq(0);
            var htmlId = response.attr("id");
            if (htmlId) {
                $("#" + htmlId).html(response.html());
            }
        }
        return response;
    }


    YzAdmin.openDialog = function(href, title) {
        /*
        On dialog load, a JQuery event 'yz-dialog-loaded' is triggered on document,,
            which can be handled in the dialog's HTML template
         */
        $("#dialog")
            .html("")
            .addClass('ajax-loading')
            .one('dialogopen', function() {
                $.get(href, function(response) {
                    response = YzAdmin.parseAjaxResponse(response);
                    $("#dialog")
                        .html(response)
                        .removeClass('ajax-loading');
                    YzAdmin.setupFormFields();
                    YzAdmin.setupFormCallback();
                    try {
                        $("#dialog").find("input[type=text], textarea").get(0).focus();
                    } catch(ex) {}
                    $(document).trigger("yz-dialog-loaded");
                });
            })
            .dialog({ title: title })
            .dialog('open');
        return YzAdmin;
    }

    YzAdmin.closeDialog = function() {
        $("#dialog").dialog('close');
        return YzAdmin;
    }

    YzAdmin.setupAutoComplete = function() {
        var ac_input = $("#autocomplete");
        if (ac_input.length > 0) {
            ac_input.autocomplete({
                'source': ac_input.attr("autocomplete-url"),
                _last: null
            });
        }
        return YzAdmin;
    }


    // ### On load ###
    $(function(){

        $.ajaxSetup({
            beforeSend: YzAdmin.beforeAjaxSendCallback,
            cache: false,
            complete: YzAdmin.AjaxCompleteCallback,
            error: YzAdmin.AjaxErrorCallback,
            success: YzAdmin.AjaxSuccessCallback,
            _last: null
        });

        // instantiate dialog
        $("#dialog").dialog({
            autoOpen: false,
            closeOnEscape: true,
            draggable: true,
            height: 300,
            modal: true,
            //position: ["center", 200]
            resizable: true,
            width: 400,
            _last: null
        });

        YzAdmin.setupAutoComplete();
        YzAdmin.setupTabs();

        YzAdmin.onHTMLLoad();

    })
})(jQuery)
